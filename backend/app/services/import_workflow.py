"""Import workflow orchestrator — runs as asyncio.create_task().

Coordinates the multi-agent pipeline: parse intent → generate problem →
verify → generate test cases → validate with Judge0 → persist to DB.
Updates import_jobs table for user-facing progress tracking.
"""

import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.config.logging import get_logger
from app.db.connection import AsyncSessionLocal
from app.db.tables import (
    Difficulty,
    ImportJob,
    ImportJobProblem,
    ImportJobStatus,
    Language,
    Problem,
    ProblemLanguage,
    TestCase,
)
from app.schemas.import_schemas import (
    GeneratedProblem,
    GeneratedTestCase,
)
from app.services.execution_validator import validate_solution_with_judge0
from app.services.import_agents import (
    get_intent_parser_agent,
    get_problem_generator_agent,
    get_problem_verifier_agent,
    get_test_case_generator_agent,
)
from app.services.seeder import title_to_slug

logger = get_logger(__name__)

MAX_RETRIES = 5
MAX_TC_RETRIES = 3
MAX_PROBLEMS_PER_IMPORT = 20
LLM_TIMEOUT_SECONDS = 120
JUDGE0_TIMEOUT_SECONDS = 60


# =============================================================================
# DB helpers — each creates its own session from the factory
# =============================================================================


async def _update_job(
    job_id: uuid.UUID,
    *,
    status: str | None = None,
    message: str | None = None,
    progress: int | None = ...,
    total: int | None = ...,
    error: str | None = ...,
    completed_at: datetime | None = ...,
) -> None:
    """Update import job fields. Uses its own DB session."""
    async with AsyncSessionLocal() as db:
        job = await db.get(ImportJob, job_id)
        if not job:
            return
        if status is not None:
            job.status = ImportJobStatus(status)
        if message is not None:
            job.message = message
        if progress is not ...:
            job.progress = progress
        if total is not ...:
            job.total = total
        if error is not ...:
            job.error = error
        if completed_at is not ...:
            job.completed_at = completed_at
        await db.commit()


async def _is_cancelled(job_id: uuid.UUID) -> bool:
    """Check if the job was cancelled by the user."""
    async with AsyncSessionLocal() as db:
        job = await db.get(ImportJob, job_id)
        return job is not None and job.status == ImportJobStatus.CANCELLED


async def _get_existing_slugs_for_pattern(pattern: str) -> list[str]:
    """Query existing problem slugs that match a pattern tag."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Problem.slug).where(Problem.pattern.contains([pattern]))
        )
        return [row[0] for row in result.fetchall()]


async def _get_existing_leetcode_nos() -> list[int]:
    """Query ALL existing leetcode_no values to prevent duplicates."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Problem.leetcode_no).where(Problem.leetcode_no.isnot(None))
        )
        return [row[0] for row in result.fetchall()]


async def _persist_problem(
    problem: GeneratedProblem,
    test_cases: list[GeneratedTestCase],
    import_job_id: uuid.UUID,
) -> str | None:
    """
    Save problem to DB and link to import job. Returns slug on success, None on failure.

    Inserts directly — does NOT use seeder's insert_problem().
    Derives slug from title via title_to_slug() for consistency.
    """
    slug = title_to_slug(problem.title)

    async with AsyncSessionLocal() as db:
        for attempt in range(3):
            try:
                max_seq_result = await db.execute(
                    select(func.max(Problem.sequence_number))
                )
                next_seq = (max_seq_result.scalar() or 0) + 1

                db_problem = Problem(
                    title=problem.title,
                    slug=slug,
                    description=problem.description,
                    difficulty=Difficulty(problem.difficulty),
                    pattern=problem.pattern,
                    sequence_number=next_seq,
                    leetcode_no=problem.leetcode_no,
                    constraints=problem.constraints,
                    examples={
                        "examples": [e.model_dump() for e in problem.examples]
                    },
                    comparison_strategy=problem.comparison_strategy,
                )
                db.add(db_problem)
                await db.flush()

                # Language configs
                for lang_key, lang_data in problem.languages.available():
                    db.add(
                        ProblemLanguage(
                            problem_id=db_problem.id,
                            language=Language(lang_key),
                            starter_code=lang_data.starter_code,
                            reference_solution=lang_data.reference_solution,
                            function_signature=lang_data.function_signature.model_dump(),
                        )
                    )

                # Test cases
                for i, tc in enumerate(test_cases):
                    db.add(
                        TestCase(
                            problem_id=db_problem.id,
                            input=tc.input,
                            expected=tc.expected,
                            sequence=i + 1,
                        )
                    )

                # Link to import job
                db.add(
                    ImportJobProblem(
                        import_job_id=import_job_id,
                        problem_id=db_problem.id,
                    )
                )

                await db.commit()
                logger.info(
                    "problem_persisted",
                    slug=slug,
                    leetcode_no=problem.leetcode_no,
                    sequence_number=next_seq,
                )
                return slug

            except IntegrityError:
                await db.rollback()
                logger.warning(
                    "persist_integrity_error",
                    slug=slug,
                    leetcode_no=problem.leetcode_no,
                    attempt=attempt + 1,
                )
                await asyncio.sleep(random.uniform(0.01, 0.1))
                continue

    return None


# =============================================================================
# Main workflow
# =============================================================================


async def import_problems_workflow(import_job_id: str, prompt: str) -> None:
    """
    Main orchestration workflow. Runs via asyncio.create_task().

    Updates import_jobs table directly for user-facing status.
    On crash, startup recovery marks stuck jobs as failed.
    """
    job_id = uuid.UUID(import_job_id)

    try:
        # ── Phase 1: Parse intent ──
        await _update_job(job_id, status="processing", message="Analyzing your request...")

        result = await asyncio.wait_for(
            get_intent_parser_agent().run(prompt),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        plan = result.output

        logger.info("import_intent_parsed", intent=plan.intent, count=plan.count)

        # Enforce max problems cap
        if plan.count > MAX_PROBLEMS_PER_IMPORT:
            plan.count = MAX_PROBLEMS_PER_IMPORT

        # For specific LeetCode imports, check if already exists
        if plan.intent == "specific" and plan.leetcode_number:
            async with AsyncSessionLocal() as db:
                existing = await db.execute(
                    select(Problem).where(
                        Problem.leetcode_no == plan.leetcode_number
                    )
                )
                if existing.scalar_one_or_none():
                    await _update_job(
                        job_id,
                        status="failed",
                        message=f"LeetCode #{plan.leetcode_number} already exists.",
                        error="duplicate",
                    )
                    return

        total = plan.count
        await _update_job(
            job_id,
            message=f"Will generate {total} problem(s)",
            progress=0,
            total=total,
        )

        # ── Phase 2: Query existing for exclusion ──
        exclude_slugs: list[str] = []
        if plan.intent == "pattern" and plan.pattern:
            exclude_slugs = await _get_existing_slugs_for_pattern(plan.pattern)

        exclude_leetcode_nos = await _get_existing_leetcode_nos()
        batch_leetcode_nos: list[int] = []

        # ── Phase 3: Generate, verify, test, persist each problem ──
        succeeded = 0
        failed = 0

        for i in range(total):
            # Check for cancellation
            if await _is_cancelled(job_id):
                await _update_job(
                    job_id,
                    status="cancelled",
                    message=f"Cancelled after {succeeded} problem(s)",
                    progress=succeeded,
                )
                return

            await _update_job(
                job_id,
                message=f"Generating problem {i + 1} of {total}...",
                progress=i,
            )

            all_exclude_slugs = exclude_slugs[:]
            all_exclude_nos = exclude_leetcode_nos + batch_leetcode_nos

            # ── Retry loop with targeted retries ──
            #
            # Outer loop: retries problem generation + verification.
            # Inner loop: retries ONLY test case generation + Judge0.
            # This avoids wastefully regenerating a correct problem/solution
            # when only the test cases need fixing.
            previous_problem: GeneratedProblem | None = None
            refinement_issues: list[str] = []
            problem_succeeded = False

            for attempt in range(MAX_RETRIES):
                try:
                    # 3a. Generate (or refine from verification failure)
                    if previous_problem and refinement_issues:
                        # Build refinement prompt with identity constraints
                        identity_constraint = ""
                        if plan.intent == "specific" and plan.leetcode_number:
                            identity_constraint = (
                                f"\nCRITICAL: You MUST keep this as LeetCode #{plan.leetcode_number}. "
                                f"Do NOT change the problem identity.\n"
                            )
                        gen_result = await asyncio.wait_for(
                            get_problem_generator_agent().run(
                                f"Fix these issues with the problem below: {refinement_issues}\n\n"
                                f"Original problem:\n{previous_problem.model_dump_json(indent=2)}\n\n"
                                f"Preserve what's correct. Only fix what's broken.\n"
                                f"{identity_constraint}"
                                f"Excluded slugs: {all_exclude_slugs}\n"
                                f"Excluded leetcode_nos: {all_exclude_nos}"
                            ),
                            timeout=LLM_TIMEOUT_SECONDS,
                        )
                    elif plan.intent == "specific":
                        gen_result = await asyncio.wait_for(
                            get_problem_generator_agent().run(
                                f"Generate LeetCode problem #{plan.leetcode_number} "
                                f"('{plan.problem_name or ''}') with full details. "
                                f"The leetcode_no must be {plan.leetcode_number}."
                            ),
                            timeout=LLM_TIMEOUT_SECONDS,
                        )
                    else:
                        difficulty_str = f"{plan.difficulty} " if plan.difficulty else ""
                        gen_result = await asyncio.wait_for(
                            get_problem_generator_agent().run(
                                f"Generate a {difficulty_str}{plan.pattern or ''} coding problem "
                                f"from LeetCode. It must be a REAL LeetCode problem with the "
                                f"correct leetcode_no.\n"
                                f"Do NOT use these LeetCode numbers: {all_exclude_nos}\n"
                                f"Do NOT generate problems with these slugs: {all_exclude_slugs}"
                            ),
                            timeout=LLM_TIMEOUT_SECONDS,
                        )

                    problem = gen_result.output

                    # Retry drift guard: reject if a specific import drifted
                    if plan.intent == "specific" and plan.leetcode_number:
                        if problem.leetcode_no != plan.leetcode_number:
                            logger.warning(
                                "retry_drift_detected",
                                expected=plan.leetcode_number,
                                actual=problem.leetcode_no,
                                actual_title=problem.title,
                                attempt=attempt + 1,
                            )
                            previous_problem = problem
                            refinement_issues = [
                                f"WRONG PROBLEM: You generated #{problem.leetcode_no} "
                                f"({problem.title}) but MUST generate #{plan.leetcode_number}."
                            ]
                            continue

                    # Reject unsupported comparison strategies
                    if problem.comparison_strategy in ("in_place_only", "in_place_with_length"):
                        logger.warning(
                            "unsupported_comparison_strategy_overridden",
                            title=problem.title,
                            strategy=problem.comparison_strategy,
                        )
                        problem.comparison_strategy = None

                    # 3b. Verify
                    await _update_job(
                        job_id, message=f"Verifying: {problem.title}", progress=i
                    )
                    ver_result = await asyncio.wait_for(
                        get_problem_verifier_agent().run(
                            f"Verify this problem:\n{problem.model_dump_json(indent=2)}"
                        ),
                        timeout=LLM_TIMEOUT_SECONDS,
                    )
                    verification = ver_result.output

                    if not verification.is_valid():
                        previous_problem = problem
                        refinement_issues = [verification.failed_checks_summary()]
                        logger.info(
                            "verification_failed",
                            title=problem.title,
                            issues=refinement_issues,
                            attempt=attempt + 1,
                        )
                        continue

                    # 3c+3d. Generate test cases + validate with Judge0.
                    # Inner retry loop: if Judge0 fails, only regenerate test cases.
                    python_lang = problem.languages.python
                    tc_validated = False
                    test_cases = None
                    tc_feedback: str | None = None

                    for tc_attempt in range(MAX_TC_RETRIES):
                        # Generate test cases (with feedback if retrying)
                        await _update_job(
                            job_id,
                            message=f"Generating test cases for {problem.title}"
                            + (f" (retry {tc_attempt})" if tc_attempt > 0 else ""),
                            progress=i,
                        )
                        if tc_attempt == 0:
                            tc_prompt = (
                                f"Generate test cases for:\n"
                                f"{problem.model_dump_json(indent=2)}"
                            )
                        else:
                            tc_prompt = (
                                f"Generate test cases for:\n"
                                f"{problem.model_dump_json(indent=2)}\n\n"
                                f"IMPORTANT: The previous test cases had errors when run "
                                f"against the reference solution:\n{tc_feedback}\n\n"
                                f"Fix the incorrect expected values. Make sure every expected "
                                f"value matches what the reference solution actually returns."
                            )

                        tc_result = await asyncio.wait_for(
                            get_test_case_generator_agent().run(tc_prompt),
                            timeout=LLM_TIMEOUT_SECONDS,
                        )
                        test_cases = tc_result.output.test_cases

                        # Validate with Judge0
                        if python_lang:
                            await _update_job(
                                job_id,
                                message=f"Validating solution for {problem.title}"
                                + (f" (retry {tc_attempt})" if tc_attempt > 0 else ""),
                                progress=i,
                            )
                            execution = await asyncio.wait_for(
                                validate_solution_with_judge0(
                                    reference_solution=python_lang.reference_solution,
                                    function_name=python_lang.function_signature.name,
                                    test_cases=[tc.model_dump() for tc in test_cases],
                                    comparison_strategy=problem.comparison_strategy,
                                ),
                                timeout=JUDGE0_TIMEOUT_SECONDS,
                            )
                            if execution["all_passed"]:
                                tc_validated = True
                                break
                            else:
                                tc_feedback = str(execution["failures"])
                                logger.warning(
                                    "judge0_validation_failed",
                                    title=problem.title,
                                    failures=execution["failures"],
                                    tc_attempt=tc_attempt + 1,
                                    outer_attempt=attempt + 1,
                                )
                        else:
                            # No Python lang to validate — accept as-is
                            tc_validated = True
                            break

                    if not tc_validated:
                        # Exhausted test case retries — fall back to outer retry
                        # which regenerates the problem + solution
                        previous_problem = problem
                        refinement_issues = [
                            "Test case generation failed after multiple attempts. "
                            "The reference solution may be incorrect."
                        ]
                        logger.warning(
                            "tc_retries_exhausted",
                            title=problem.title,
                            attempt=attempt + 1,
                        )
                        continue

                    # 3e. Persist
                    await _update_job(
                        job_id, message=f"Saving {problem.title}", progress=i
                    )
                    slug = await _persist_problem(problem, test_cases, job_id)

                    if slug:
                        batch_leetcode_nos.append(problem.leetcode_no)
                        all_exclude_slugs.append(slug)
                        succeeded += 1
                        problem_succeeded = True
                        break
                    else:
                        # IntegrityError on all retries — skip this problem
                        all_exclude_nos.append(problem.leetcode_no)
                        previous_problem = None
                        refinement_issues = []
                        continue

                except Exception as e:
                    logger.error(
                        "problem_generation_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    previous_problem = None
                    refinement_issues = []
                    continue

            if not problem_succeeded:
                failed += 1

        # ── Phase 4: Complete ──
        if succeeded > 0:
            msg = f"Imported {succeeded} of {total} problem(s)"
            if failed:
                msg += f" ({failed} failed)"
            await _update_job(
                job_id,
                status="completed",
                message=msg,
                progress=total,
                total=total,
                completed_at=datetime.now(UTC).replace(tzinfo=None),
            )
        else:
            await _update_job(
                job_id,
                status="failed",
                message=f"All {total} problem(s) failed to generate",
                error="All problems failed generation/validation",
            )

    except Exception as e:
        logger.error("import_workflow_error", job_id=str(job_id), error=str(e))
        await _update_job(
            job_id,
            status="failed",
            message=f"Workflow error: {str(e)[:200]}",
            error=str(e),
        )


# =============================================================================
# Startup recovery
# =============================================================================


RECOVERY_STALENESS_MINUTES = 5


async def recover_stuck_import_jobs() -> None:
    """
    Mark import jobs stuck in 'processing' as failed on app startup.

    Called from the FastAPI lifespan to handle cases where the process
    crashed or was restarted while an import was in progress.

    Only marks jobs as failed if updated_at is older than RECOVERY_STALENESS_MINUTES
    to avoid incorrectly marking recently-created jobs during fast restarts.
    """
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=RECOVERY_STALENESS_MINUTES)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ImportJob).where(
                ImportJob.status.in_([
                    ImportJobStatus.QUEUED,
                    ImportJobStatus.PROCESSING,
                ]),
                ImportJob.updated_at < cutoff,
            )
        )
        stuck_jobs = result.scalars().all()

        for job in stuck_jobs:
            job.status = ImportJobStatus.FAILED
            job.message = "Interrupted by server restart — please retry"
            job.error = "Server restarted while import was in progress"
            logger.warning("recovered_stuck_import_job", job_id=str(job.id))

        if stuck_jobs:
            await db.commit()
            logger.info("recovered_stuck_jobs", count=len(stuck_jobs))
