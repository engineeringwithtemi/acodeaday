"""Pydantic schemas for the AI-powered problem import feature."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# Agent Output Schemas (structured LLM output types)
# =============================================================================


class ImportPlan(BaseModel):
    """Parsed user intent from natural language prompt."""

    intent: Literal["pattern", "specific"]
    pattern: str | None = None
    problem_name: str | None = None
    leetcode_number: int | None = None
    count: int = 1
    difficulty: str | None = None


class GeneratedProblemLanguage(BaseModel):
    """Language-specific code for a generated problem."""

    starter_code: str
    reference_solution: str
    function_signature: dict = Field(
        description='{"name": "funcName", "params": [{"name": "x", "type": "int"}], "return_type": "int"}'
    )


class GeneratedProblemExample(BaseModel):
    """A problem example with input, output, and optional explanation."""

    input: str
    output: str
    explanation: str | None = None


class GeneratedProblem(BaseModel):
    """Full generated problem matching existing DB schema."""

    title: str
    difficulty: Literal["easy", "medium", "hard"]
    pattern: list[str]
    description: str
    constraints: list[str]
    examples: list[GeneratedProblemExample]
    languages: dict[str, GeneratedProblemLanguage]
    leetcode_no: int = Field(description="The real LeetCode problem number")
    comparison_strategy: str | None = Field(
        default=None,
        description='Comparison strategy: null for exact, "unordered_array" for order-independent',
    )


class GeneratedTestCase(BaseModel):
    """A single test case with function arguments and expected output."""

    input: list[Any] = Field(description="Function arguments as array")
    expected: Any = Field(description="Expected return value")


class GeneratedTestCases(BaseModel):
    """Output from test case generator agent."""

    test_cases: list[GeneratedTestCase]
    edge_cases_covered: list[str] = Field(description="Description of edge cases covered")


class VerificationResult(BaseModel):
    """Output from problem verifier agent."""

    valid: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# =============================================================================
# API Request/Response Schemas
# =============================================================================


class ImportRequest(BaseModel):
    """Request body for starting an import."""

    prompt: str = Field(..., min_length=3, max_length=500)


class ImportedProblemResponse(BaseModel):
    """A problem linked to an import job — clickable to /problem/:slug."""

    id: UUID
    title: str
    slug: str
    difficulty: str
    pattern: list[str]

    model_config = {"from_attributes": True}


class ImportJobResponse(BaseModel):
    """Response after creating an import job."""

    id: UUID
    prompt: str
    status: str
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportJobDetailResponse(BaseModel):
    """Full import job detail with linked problems."""

    id: UUID
    prompt: str
    status: str
    message: str | None
    progress: int | None
    total: int | None
    problems: list[ImportedProblemResponse]
    created_at: datetime
    completed_at: datetime | None


class ImportJobSummaryResponse(BaseModel):
    """Summary for import job list view."""

    id: UUID
    prompt: str
    status: str
    message: str | None
    progress: int | None
    total: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
