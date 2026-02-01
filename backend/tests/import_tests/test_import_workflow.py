"""Tests for the import workflow orchestrator."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    FunctionParam,
    FunctionSignature,
    GeneratedProblem,
    GeneratedProblemExample,
    GeneratedProblemLanguage,
    GeneratedProblemLanguages,
    GeneratedTestCase,
)
from app.services.import_workflow import (
    _is_cancelled,
    _persist_problem,
    _update_job,
    recover_stuck_import_jobs,
)


@pytest.fixture
async def workflow_job(test_db: AsyncSession, test_user_id: str) -> ImportJob:
    """Create import job for workflow testing."""
    job = ImportJob(
        id=uuid.uuid4(),
        user_id=test_user_id,
        prompt="Test workflow",
        status=ImportJobStatus.QUEUED,
        message="Queued",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
    return job


def _make_generated_problem(
    title: str = "Two Sum",
    leetcode_no: int = 1,
    difficulty: str = "easy",
) -> GeneratedProblem:
    """Helper to create a valid GeneratedProblem."""
    return GeneratedProblem(
        title=title,
        difficulty=difficulty,
        pattern=["hash-map"],
        description="Given an array of integers nums and an integer target...",
        constraints=["2 <= nums.length <= 10^4"],
        examples=[
            GeneratedProblemExample(
                input="nums = [2,7,11,15], target = 9",
                output="[0,1]",
                explanation="nums[0] + nums[1] = 2 + 7 = 9",
            )
        ],
        languages=GeneratedProblemLanguages(
            python=GeneratedProblemLanguage(
                starter_code="class Solution:\n    def twoSum(self, nums, target):\n        pass",
                reference_solution="class Solution:\n    def twoSum(self, nums, target):\n        lookup = {}\n        for i, n in enumerate(nums):\n            if target - n in lookup:\n                return [lookup[target-n], i]\n            lookup[n] = i",
                function_signature=FunctionSignature(
                    name="twoSum",
                    params=[
                        FunctionParam(name="nums", type="List[int]"),
                        FunctionParam(name="target", type="int"),
                    ],
                    return_type="List[int]",
                ),
            )
        ),
        leetcode_no=leetcode_no,
        comparison_strategy=None,
    )


def _make_test_cases() -> list[GeneratedTestCase]:
    """Helper to create valid test cases."""
    return [
        GeneratedTestCase(input=[[2, 7, 11, 15], 9], expected=[0, 1]),
        GeneratedTestCase(input=[[3, 2, 4], 6], expected=[1, 2]),
    ]


# ── _update_job ──


@pytest.mark.asyncio
async def test_update_job_status(
    workflow_job: ImportJob,
    test_db: AsyncSession,
):
    """Test updating job status via _update_job."""
    await _update_job(
        workflow_job.id,
        status="processing",
        message="Working on it...",
        progress=1,
        total=5,
    )

    # Refresh from DB to verify
    await test_db.refresh(workflow_job)
    assert workflow_job.status == ImportJobStatus.PROCESSING
    assert workflow_job.message == "Working on it..."
    assert workflow_job.progress == 1
    assert workflow_job.total == 5


@pytest.mark.asyncio
async def test_update_job_nonexistent():
    """Test updating non-existent job is a no-op."""
    # Should not raise
    await _update_job(
        uuid.uuid4(),
        status="failed",
        message="Should not exist",
    )


# ── _is_cancelled ──


@pytest.mark.asyncio
async def test_is_cancelled_false(workflow_job: ImportJob):
    """Test _is_cancelled returns False for non-cancelled job."""
    result = await _is_cancelled(workflow_job.id)
    assert result is False


@pytest.mark.asyncio
async def test_is_cancelled_true(test_db: AsyncSession, test_user_id: str):
    """Test _is_cancelled returns True for cancelled job."""
    job = ImportJob(
        user_id=test_user_id,
        prompt="Cancel me",
        status=ImportJobStatus.CANCELLED,
        message="Cancelled",
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)

    result = await _is_cancelled(job.id)
    assert result is True


# ── _persist_problem ──


@pytest.mark.asyncio
async def test_persist_problem_success(
    workflow_job: ImportJob,
    test_db: AsyncSession,
):
    """Test persisting a generated problem creates all DB records."""
    problem = _make_generated_problem()
    test_cases = _make_test_cases()

    slug = await _persist_problem(problem, test_cases, workflow_job.id)

    assert slug == "two-sum"

    # Verify problem in DB
    result = await test_db.execute(select(Problem).where(Problem.slug == "two-sum"))
    db_problem = result.scalar_one()
    assert db_problem.title == "Two Sum"
    assert db_problem.leetcode_no == 1
    assert db_problem.difficulty == Difficulty.EASY

    # Verify language config
    lang_result = await test_db.execute(
        select(ProblemLanguage).where(ProblemLanguage.problem_id == db_problem.id)
    )
    langs = lang_result.scalars().all()
    assert len(langs) == 1
    assert langs[0].language == Language.PYTHON
    # Verify function_signature stored as dict (from model_dump())
    assert langs[0].function_signature["name"] == "twoSum"
    assert len(langs[0].function_signature["params"]) == 2

    # Verify test cases
    tc_result = await test_db.execute(select(TestCase).where(TestCase.problem_id == db_problem.id))
    tcs = tc_result.scalars().all()
    assert len(tcs) == 2

    # Verify import job link
    link_result = await test_db.execute(
        select(ImportJobProblem).where(ImportJobProblem.import_job_id == workflow_job.id)
    )
    links = link_result.scalars().all()
    assert len(links) == 1
    assert links[0].problem_id == db_problem.id


@pytest.mark.asyncio
async def test_persist_problem_duplicate_slug(
    workflow_job: ImportJob,
    test_db: AsyncSession,
):
    """Test persisting a problem with duplicate slug fails gracefully."""
    # Create existing problem with slug "two-sum"
    existing = Problem(
        title="Two Sum",
        slug="two-sum",
        description="Existing",
        difficulty=Difficulty.EASY,
        pattern=["hash-map"],
        sequence_number=1,
        constraints=[],
        examples={"examples": []},
        leetcode_no=1,
    )
    test_db.add(existing)
    await test_db.commit()

    problem = _make_generated_problem()
    test_cases = _make_test_cases()

    # Should return None due to IntegrityError
    slug = await _persist_problem(problem, test_cases, workflow_job.id)
    assert slug is None


# ── recover_stuck_import_jobs ──


@pytest.mark.asyncio
async def test_recover_stuck_jobs(test_db: AsyncSession, test_user_id: str):
    """Test startup recovery marks stuck jobs as failed.

    Jobs must be older than RECOVERY_STALENESS_MINUTES to be recovered,
    so we set updated_at to 10 minutes ago.
    """
    old_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10)

    # Create stuck jobs with old timestamps
    queued_job = ImportJob(
        user_id=test_user_id,
        prompt="Stuck queued",
        status=ImportJobStatus.QUEUED,
        updated_at=old_time,
    )
    processing_job = ImportJob(
        user_id=test_user_id,
        prompt="Stuck processing",
        status=ImportJobStatus.PROCESSING,
        updated_at=old_time,
    )
    completed_job = ImportJob(
        user_id=test_user_id,
        prompt="Already done",
        status=ImportJobStatus.COMPLETED,
        message="Done",
    )
    test_db.add_all([queued_job, processing_job, completed_job])
    await test_db.commit()

    await recover_stuck_import_jobs()

    # Refresh and check
    await test_db.refresh(queued_job)
    await test_db.refresh(processing_job)
    await test_db.refresh(completed_job)

    assert queued_job.status == ImportJobStatus.FAILED
    assert "restart" in queued_job.message.lower()

    assert processing_job.status == ImportJobStatus.FAILED
    assert "restart" in processing_job.message.lower()

    # Completed job should NOT be touched
    assert completed_job.status == ImportJobStatus.COMPLETED


@pytest.mark.asyncio
async def test_recover_skips_recent_jobs(test_db: AsyncSession, test_user_id: str):
    """Test that recovery does NOT mark recently-created jobs as failed."""
    # Create a job with default updated_at (now) — should NOT be recovered
    recent_job = ImportJob(
        user_id=test_user_id,
        prompt="Just started",
        status=ImportJobStatus.PROCESSING,
    )
    test_db.add(recent_job)
    await test_db.commit()

    await recover_stuck_import_jobs()

    await test_db.refresh(recent_job)
    # Should still be processing — not old enough to recover
    assert recent_job.status == ImportJobStatus.PROCESSING
