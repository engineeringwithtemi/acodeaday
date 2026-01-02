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


class ProgressResponse(BaseModel):
    """Overview of user's progress across all Blind 75."""

    total_problems: int = Field(..., description="Total problems in dataset (75)")
    solved_count: int = Field(..., description="Problems solved at least once")
    mastered_count: int = Field(..., description="Problems mastered (solved 2x)")
    in_progress_count: int = Field(..., description="Problems solved once, not mastered")
    unsolved_count: int = Field(..., description="Problems never attempted")
    due_for_review: int = Field(..., description="Problems due for review today")

    problems_by_difficulty: dict[str, int] = Field(
        ..., description="Breakdown by difficulty"
    )
    problems_by_pattern: dict[str, int] = Field(..., description="Breakdown by pattern")


class MasteredProblemSchema(BaseModel):
    """Schema for mastered problems list."""

    id: UUID
    title: str
    slug: str
    difficulty: Difficulty
    pattern: str
    sequence_number: int
    times_solved: int
    last_solved_at: datetime
    show_again: bool  # Whether user wants to review again

    model_config = {"from_attributes": True}


class SubmissionSchema(BaseModel):
    """Schema for submission history."""

    id: UUID
    problem_id: UUID
    problem_title: str
    code: str
    language: str
    passed: bool
    runtime_ms: int | None
    submitted_at: datetime

    model_config = {"from_attributes": True}
