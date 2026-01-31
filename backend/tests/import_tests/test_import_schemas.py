"""Tests for import Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.import_schemas import (
    GeneratedProblem,
    GeneratedProblemExample,
    GeneratedProblemLanguage,
    GeneratedTestCase,
    GeneratedTestCases,
    ImportPlan,
    ImportRequest,
    VerificationResult,
)


# ── ImportPlan ──


def test_import_plan_pattern():
    """Test creating a pattern import plan."""
    plan = ImportPlan(
        intent="pattern",
        pattern="sliding-window",
        count=5,
        difficulty="medium",
    )
    assert plan.intent == "pattern"
    assert plan.count == 5
    assert plan.pattern == "sliding-window"


def test_import_plan_specific():
    """Test creating a specific problem import plan."""
    plan = ImportPlan(
        intent="specific",
        leetcode_number=1,
        problem_name="Two Sum",
    )
    assert plan.intent == "specific"
    assert plan.leetcode_number == 1


def test_import_plan_invalid_intent():
    """Test that invalid intent raises validation error."""
    with pytest.raises(ValidationError):
        ImportPlan(intent="invalid")


# ── GeneratedProblem ──


def test_generated_problem_valid():
    """Test creating a valid generated problem."""
    problem = GeneratedProblem(
        title="Two Sum",
        difficulty="easy",
        pattern=["hash-map", "array"],
        description="Find two numbers that add up to target",
        constraints=["2 <= nums.length <= 10^4"],
        examples=[
            GeneratedProblemExample(
                input="nums = [2,7,11,15], target = 9",
                output="[0,1]",
            )
        ],
        languages={
            "python": GeneratedProblemLanguage(
                starter_code="pass",
                reference_solution="return [0,1]",
                function_signature={"name": "twoSum", "params": [], "return_type": "list"},
            )
        },
        leetcode_no=1,
    )
    assert problem.title == "Two Sum"
    assert problem.leetcode_no == 1
    assert problem.comparison_strategy is None


def test_generated_problem_invalid_difficulty():
    """Test that invalid difficulty raises validation error."""
    with pytest.raises(ValidationError):
        GeneratedProblem(
            title="Test",
            difficulty="extreme",
            pattern=[],
            description="test",
            constraints=[],
            examples=[],
            languages={},
            leetcode_no=1,
        )


def test_generated_problem_requires_leetcode_no():
    """Test that leetcode_no is required."""
    with pytest.raises(ValidationError):
        GeneratedProblem(
            title="Test",
            difficulty="easy",
            pattern=[],
            description="test",
            constraints=[],
            examples=[],
            languages={},
        )


# ── GeneratedTestCase ──


def test_generated_test_case():
    """Test creating a test case."""
    tc = GeneratedTestCase(input=[[2, 7, 11, 15], 9], expected=[0, 1])
    assert tc.input == [[2, 7, 11, 15], 9]
    assert tc.expected == [0, 1]


def test_generated_test_cases_collection():
    """Test creating a test case collection."""
    collection = GeneratedTestCases(
        test_cases=[
            GeneratedTestCase(input=[[1, 2], 3], expected=[0, 1]),
        ],
        edge_cases_covered=["empty array", "single element"],
    )
    assert len(collection.test_cases) == 1
    assert len(collection.edge_cases_covered) == 2


# ── VerificationResult ──


def test_verification_result_valid():
    """Test valid verification result."""
    result = VerificationResult(valid=True)
    assert result.valid is True
    assert result.issues == []


def test_verification_result_with_issues():
    """Test verification result with issues."""
    result = VerificationResult(
        valid=False,
        issues=["Wrong difficulty", "Missing constraint"],
        suggestions=["Change to medium"],
    )
    assert not result.valid
    assert len(result.issues) == 2


# ── ImportRequest ──


def test_import_request_valid():
    """Test valid import request."""
    req = ImportRequest(prompt="Add 5 sliding window problems")
    assert req.prompt == "Add 5 sliding window problems"


def test_import_request_too_short():
    """Test import request with too-short prompt."""
    with pytest.raises(ValidationError):
        ImportRequest(prompt="ab")


def test_import_request_too_long():
    """Test import request with too-long prompt."""
    with pytest.raises(ValidationError):
        ImportRequest(prompt="x" * 501)
