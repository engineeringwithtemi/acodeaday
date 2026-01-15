"""Pydantic schemas for code execution."""

from typing import Any

from pydantic import BaseModel, Field

from app.db.tables import Language


class RunCodeRequest(BaseModel):
    """Request to run code against example test cases."""

    problem_slug: str = Field(..., description="Problem slug identifier")
    code: str = Field(..., description="User's code to execute")
    language: Language = Field(..., description="Programming language")
    custom_input: list[list[Any]] | None = Field(
        None, description="Custom test inputs (if provided, runs against these instead of DB test cases)"
    )


class TestResult(BaseModel):
    """Result from a single test case."""

    test_number: int
    passed: bool
    input: dict | list | str | int | float | bool | None = None
    output: dict | list | str | int | float | bool | None = None
    expected: dict | list | str | int | float | bool | None = None
    error: str | None = None
    error_type: str | None = None
    stdout: str | None = None  # Captured print() output from user code


class RunCodeResponse(BaseModel):
    """Response from running code."""

    success: bool = Field(..., description="Whether execution succeeded")
    results: list[TestResult] = Field(..., description="Test case results")
    summary: dict = Field(..., description="Summary stats (total, passed, failed)")
    stdout: str | None = Field(None, description="Raw stdout from Judge0")
    stderr: str | None = Field(None, description="Raw stderr from Judge0")
    compile_error: str | None = Field(None, description="Compilation errors if any")
    runtime_error: str | None = Field(None, description="Runtime errors if any")


class SubmitCodeRequest(BaseModel):
    """Request to submit code (runs all test cases)."""

    problem_slug: str = Field(..., description="Problem slug identifier")
    code: str = Field(..., description="User's code to execute")
    language: Language = Field(..., description="Programming language")


class SubmitCodeResponse(BaseModel):
    """Response from code submission."""

    success: bool = Field(..., description="Whether all tests passed")
    results: list[TestResult] = Field(..., description="All test results")
    summary: dict = Field(..., description="Summary stats (total executed, passed, failed)")
    total_test_cases: int = Field(..., description="Total test cases in problem (for X/Y display)")
    submission_id: str = Field(..., description="Submission record ID")
    runtime_ms: int | None = Field(None, description="Execution time in milliseconds")
    memory_kb: int | None = Field(None, description="Memory usage in kilobytes")
    compile_error: str | None = Field(None, description="Compilation errors if any")
    runtime_error: str | None = Field(None, description="Runtime errors if any")

    # Anki spaced repetition fields
    needs_rating: bool = Field(False, description="Whether user needs to rate difficulty")
    times_solved: int | None = Field(None, description="Number of times solved")
    is_mastered: bool | None = Field(None, description="Whether problem is mastered")
    next_review_date: str | None = Field(None, description="Next review date (ISO format)")
    interval_days: int | None = Field(None, description="Current interval in days")
    ease_factor: float | None = Field(None, description="Current ease factor")


class RatingRequest(BaseModel):
    """Request to rate a submission difficulty."""

    problem_slug: str = Field(..., description="Problem slug identifier")
    rating: str = Field(..., description="Difficulty rating: again, hard, good, or mastered")


class RatingResponse(BaseModel):
    """Response from rating a submission."""

    success: bool = Field(..., description="Whether rating was applied")
    interval_days: int = Field(..., description="New interval in days until next review")
    ease_factor: float = Field(..., description="Updated ease factor")
    next_review_date: str | None = Field(None, description="Next review date (ISO format)")
    is_mastered: bool = Field(..., description="Whether problem is now mastered")
    review_count: int = Field(..., description="Total number of reviews")
    times_solved: int = Field(..., description="Total times solved")
