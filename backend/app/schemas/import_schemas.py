"""Pydantic schemas for the AI-powered problem import feature.

All agent output schemas are designed for OpenAI strict-mode compatibility:
- No bare `dict` types (must use explicit models with typed fields)
- No `Any` types (must use explicit unions so every schema node has a `type` key)
- No `dict[str, Model]` (generates `$ref` in `additionalProperties` which OpenAI rejects)
"""

from datetime import datetime
from typing import Literal
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


class FunctionParam(BaseModel):
    """A single function parameter with name and type annotation."""

    name: str
    type: str


class FunctionSignature(BaseModel):
    """Function signature metadata for a coding problem."""

    name: str
    params: list[FunctionParam]
    return_type: str


class GeneratedProblemLanguage(BaseModel):
    """Language-specific code for a generated problem."""

    starter_code: str
    reference_solution: str
    function_signature: FunctionSignature


class GeneratedProblemLanguages(BaseModel):
    """Language implementations. Python is required."""

    python: GeneratedProblemLanguage
    javascript: GeneratedProblemLanguage | None = None

    def available(self) -> list[tuple[str, GeneratedProblemLanguage]]:
        """Return (language_key, data) pairs for non-None languages."""
        result: list[tuple[str, GeneratedProblemLanguage]] = [("python", self.python)]
        if self.javascript:
            result.append(("javascript", self.javascript))
        return result


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
    languages: GeneratedProblemLanguages
    leetcode_no: int = Field(description="The real LeetCode problem number")
    comparison_strategy: str | None = Field(
        default=None,
        description='Comparison strategy: null for exact, "unordered_array" for order-independent',
    )


# Test case value types — explicit unions for OpenAI strict-mode compatibility.
# Covers all practical LeetCode I/O types: primitives, 1D arrays, and 2D arrays.
_Atom = int | float | str | bool | None
_TestValue = _Atom | list[_Atom | list[_Atom]]


class GeneratedTestCase(BaseModel):
    """A single test case with function arguments and expected output."""

    input: list[_TestValue] = Field(description="Function arguments as array")
    expected: _TestValue = Field(description="Expected return value")


class GeneratedTestCases(BaseModel):
    """Output from test case generator agent."""

    test_cases: list[GeneratedTestCase]
    edge_cases_covered: list[str] = Field(description="Description of edge cases covered")


class VerificationResult(BaseModel):
    """Output from problem verifier agent.

    Uses structured boolean fields per check instead of free-form issues list.
    This prevents models from confusing positive observations with errors.
    Validity is computed from the boolean fields, not trusted from the LLM.
    """

    title_correct: bool = Field(
        description="true if the title matches a real LeetCode problem"
    )
    leetcode_no_correct: bool = Field(
        description="true if leetcode_no is the correct number for this problem title"
    )
    description_correct: bool = Field(
        description="true if description is clear and matches the real LeetCode problem"
    )
    solution_correct: bool = Field(
        description="true if the reference solution is correct and would pass on LeetCode"
    )
    signature_matches: bool = Field(
        description="true if function_signature matches the solution's method name and parameters"
    )
    starter_code_correct: bool = Field(
        description="true if starter code has the correct method signature with pass body"
    )
    constraints_correct: bool = Field(
        description="true if constraints are realistic and match the actual problem"
    )
    examples_correct: bool = Field(
        description="true if all examples have correct input/output pairs"
    )
    difficulty_correct: bool = Field(
        description="true if difficulty matches the actual LeetCode difficulty"
    )
    comparison_strategy_correct: bool = Field(
        description="true if comparison_strategy is appropriate for this problem"
    )
    error_details: str = Field(
        default="",
        description="If any check is false, explain what is wrong. Empty string if all pass.",
    )

    def is_valid(self) -> bool:
        """Compute validity from individual check fields."""
        return all([
            self.title_correct,
            self.leetcode_no_correct,
            self.description_correct,
            self.solution_correct,
            self.signature_matches,
            self.starter_code_correct,
            self.constraints_correct,
            self.examples_correct,
            self.difficulty_correct,
            self.comparison_strategy_correct,
        ])

    def failed_checks_summary(self) -> str:
        """Build a summary of failed checks for refinement prompts."""
        check_names = {
            "title": self.title_correct,
            "leetcode_no": self.leetcode_no_correct,
            "description": self.description_correct,
            "solution": self.solution_correct,
            "signature": self.signature_matches,
            "starter_code": self.starter_code_correct,
            "constraints": self.constraints_correct,
            "examples": self.examples_correct,
            "difficulty": self.difficulty_correct,
            "comparison_strategy": self.comparison_strategy_correct,
        }
        failed = [name for name, passed in check_names.items() if not passed]
        summary = f"Failed checks: {', '.join(failed)}"
        if self.error_details:
            summary += f". Details: {self.error_details}"
        return summary


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
