"""Import workflow orchestrator — runs as asyncio.create_task().

Coordinates the multi-agent pipeline: parse intent → generate problem →
verify → generate test cases → validate with Judge0 → persist to DB.
Updates import_jobs table for user-facing progress tracking.
"""

import uuid
from datetime import UTC, datetime

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

MAX_RETRIES = 3
MAX_PROBLEMS_PER_IMPORT = 20


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
                for lang_key, lang_data in problem.languages.items():
                    db.add(
                        ProblemLanguage(
                            problem_id=db_problem.id,
                            language=Language(lang_key),
                            starter_code=lang_data.starter_code,
                            reference_solution=lang_data.reference_solution,
                            function_signature=lang_data.function_signature,
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

        result = await get_intent_parser_agent().run(prompt)
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

            # ── Retry loop with refinement ──
            previous_problem: GeneratedProblem | None = None
            issues: list[str] = []
            problem_succeeded = False

            for attempt in range(MAX_RETRIES):
                try:
                    # 3a. Generate (or refine)
                    if previous_problem and issues:
                        gen_result = await get_problem_generator_agent().run(
                            f"Fix these issues with the problem below: {issues}\n\n"
                            f"Original problem:\n{previous_problem.model_dump_json(indent=2)}\n\n"
                            f"Preserve what's correct. Only fix what's broken.\n"
                            f"Excluded slugs: {all_exclude_slugs}\n"
                            f"Excluded leetcode_nos: {all_exclude_nos}"
                        )
                    elif plan.intent == "specific":
                        gen_result = await get_problem_generator_agent().run(
                            f"Generate LeetCode problem #{plan.leetcode_number} "
                            f"('{plan.problem_name or ''}') with full details. "
                            f"The leetcode_no must be {plan.leetcode_number}."
                        )
                    else:
                        difficulty_str = f"{plan.difficulty} " if plan.difficulty else ""
                        gen_result = await get_problem_generator_agent().run(
                            f"Generate a {difficulty_str}{plan.pattern or ''} coding problem "
                            f"from LeetCode. It must be a REAL LeetCode problem with the "
                            f"correct leetcode_no.\n"
                            f"Do NOT use these LeetCode numbers: {all_exclude_nos}\n"
                            f"Do NOT generate problems with these slugs: {all_exclude_slugs}"
                        )

                    problem = gen_result.output

                    # Reject unsupported comparison strategies
                    if problem.comparison_strategy in ("in_place_only", "in_place_with_length"):
                        problem.comparison_strategy = None

                    # 3b. Verify
                    await _update_job(
                        job_id, message=f"Verifying: {problem.title}", progress=i
                    )
                    ver_result = await get_problem_verifier_agent().run(
                        f"Verify this problem:\n{problem.model_dump_json(indent=2)}"
                    )
                    verification = ver_result.output

                    if not verification.valid:
                        previous_problem = problem
                        issues = verification.issues
                        logger.info(
                            "verification_failed",
                            title=problem.title,
                            issues=verification.issues,
                            attempt=attempt + 1,
                        )
                        continue

                    # 3c. Generate test cases
                    await _update_job(
                        job_id,
                        message=f"Generating test cases for {problem.title}",
                        progress=i,
                    )
                    tc_result = await get_test_case_generator_agent().run(
                        f"Generate test cases for:\n{problem.model_dump_json(indent=2)}"
                    )
                    test_cases = tc_result.output.test_cases

                    # 3d. Validate with Judge0
                    python_lang = problem.languages.get("python")
                    if python_lang:
                        await _update_job(
                            job_id,
                            message=f"Validating solution for {problem.title}",
                            progress=i,
                        )
                        execution = await validate_solution_with_judge0(
                            reference_solution=python_lang.reference_solution,
                            function_name=python_lang.function_signature.get("name", ""),
                            test_cases=[tc.model_dump() for tc in test_cases],
                            comparison_strategy=problem.comparison_strategy,
                        )
                        if not execution["all_passed"]:
                            previous_problem = problem
                            issues = [
                                f"Judge0 validation failed: {execution['failures']}"
                            ]
                            logger.warning(
                                "judge0_validation_failed",
                                title=problem.title,
                                failures=execution["failures"],
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
                        issues = []
                        continue

                except Exception as e:
                    logger.error(
                        "problem_generation_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    previous_problem = None
                    issues = []
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


async def recover_stuck_import_jobs() -> None:
    """
    Mark import jobs stuck in 'processing' as failed on app startup.

    Called from the FastAPI lifespan to handle cases where the process
    crashed or was restarted while an import was in progress.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ImportJob).where(
                ImportJob.status.in_([
                    ImportJobStatus.QUEUED,
                    ImportJobStatus.PROCESSING,
                ])
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
