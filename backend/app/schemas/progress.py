"""Pydantic schemas for user progress and spaced repetition."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.tables import Difficulty


class UserProgressSchema(BaseModel):
    """User's progress on a specific problem."""

    problem_id: UUID
    times_solved: int
    last_solved_at: datetime | None
    next_review_date: date | None
    is_mastered: bool
    show_again: bool

    model_config = {"from_attributes": True}


class ProblemProgressSchema(BaseModel):
    """Problem with user's progress info."""

    # Problem info
    id: UUID
    title: str
    slug: str
    difficulty: Difficulty
    pattern: str
    sequence_number: int

    # User progress
    times_solved: int = 0
    last_solved_at: datetime | None = None
    next_review_date: date | None = None
    is_mastered: bool = False


class TodaySessionResponse(BaseModel):
    """
    Daily session response with up to 3 problems.

    Includes 2 review problems (if due) + 1 new problem.
    """

    review_problems: list[ProblemProgressSchema] = Field(
        ..., description="Problems due for review (max 2)"
    )
    new_problem: ProblemProgressSchema | None = Field(
        None, description="Next unsolved problem"
    )
    total_mastered: int = Field(..., description="Total mastered problems")
    total_solved: int = Field(..., description="Total problems solved at least once")


# --- Schemas for /api/progress endpoint ---


class ProblemBasicSchema(BaseModel):
    """Basic problem info for progress list."""

    id: UUID
    title: str
    slug: str
    difficulty: Difficulty
    pattern: str
    sequence_number: int

    model_config = {"from_attributes": True}


class UserProgressBasicSchema(BaseModel):
    """User progress info for progress list."""

    times_solved: int
    last_solved_at: datetime | None
    next_review_date: date | None
    is_mastered: bool
    show_again: bool

    model_config = {"from_attributes": True}


class ProblemWithProgressSchema(BaseModel):
    """Problem with its user progress (nested structure for frontend)."""

    problem: ProblemBasicSchema
    user_progress: UserProgressBasicSchema | None


class ProgressResponse(BaseModel):
    """Overview of user's progress across all Blind 75."""

    problems: list[ProblemWithProgressSchema] = Field(
        ..., description="All problems with user progress"
    )
    total_problems: int = Field(..., description="Total problems in dataset (75)")
    completed_problems: int = Field(..., description="Problems solved at least once")
    mastered_problems: int = Field(..., description="Problems mastered (solved 2x)")


class SubmissionBasicSchema(BaseModel):
    """Basic submission info for mastered problems."""

    id: UUID
    code: str
    language: str
    passed: bool
    runtime_ms: int | None
    memory_kb: int | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class MasteredProblemSchema(BaseModel):
    """Schema for mastered problems list (nested structure for frontend)."""

    problem: ProblemBasicSchema
    user_progress: UserProgressBasicSchema
    last_submission: SubmissionBasicSchema | None


class MasteredProblemsResponse(BaseModel):
    """Response wrapper for mastered problems list."""

    mastered_problems: list[MasteredProblemSchema]


class SubmissionSchema(BaseModel):
    """Schema for submission history."""

    id: UUID
    problem_id: UUID
    problem_title: str
    code: str
    language: str
    passed: bool
    runtime_ms: int | None
    memory_kb: int | None
    submitted_at: datetime

    # Test result summary
    total_test_cases: int = 0
    passed_count: int = 0

    # First failed test details (None if all passed)
    failed_test_number: int | None = None
    failed_input: dict | list | None = None
    failed_output: dict | list | int | float | str | bool | None = None
    failed_expected: dict | list | int | float | str | bool | None = None
    failed_is_hidden: bool = False

    model_config = {"from_attributes": True}


class ShowAgainResponse(BaseModel):
    """Response from marking a problem to show again."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
