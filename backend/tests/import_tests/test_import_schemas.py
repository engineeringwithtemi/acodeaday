"""Tests for import Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.import_schemas import (
    FunctionParam,
    FunctionSignature,
    GeneratedProblem,
    GeneratedProblemExample,
    GeneratedProblemLanguage,
    GeneratedProblemLanguages,
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


# ── FunctionSignature ──


def test_function_signature():
    """Test creating a function signature with typed params."""
    sig = FunctionSignature(
        name="twoSum",
        params=[
            FunctionParam(name="nums", type="List[int]"),
            FunctionParam(name="target", type="int"),
        ],
        return_type="List[int]",
    )
    assert sig.name == "twoSum"
    assert len(sig.params) == 2
    assert sig.params[0].name == "nums"


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
        languages=GeneratedProblemLanguages(
            python=GeneratedProblemLanguage(
                starter_code="pass",
                reference_solution="return [0,1]",
                function_signature=FunctionSignature(
                    name="twoSum",
                    params=[],
                    return_type="list",
                ),
            ),
        ),
        leetcode_no=1,
    )
    assert problem.title == "Two Sum"
    assert problem.leetcode_no == 1
    assert problem.comparison_strategy is None
    assert problem.languages.python.function_signature.name == "twoSum"


def test_generated_problem_languages_available():
    """Test the languages.available() helper."""
    lang = GeneratedProblemLanguage(
        starter_code="pass",
        reference_solution="return 1",
        function_signature=FunctionSignature(
            name="f", params=[], return_type="int"
        ),
    )
    # Python only
    langs = GeneratedProblemLanguages(python=lang)
    available = langs.available()
    assert len(available) == 1
    assert available[0][0] == "python"

    # Python + JavaScript
    langs_both = GeneratedProblemLanguages(python=lang, javascript=lang)
    available_both = langs_both.available()
    assert len(available_both) == 2
    assert available_both[1][0] == "javascript"


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
            languages=GeneratedProblemLanguages(
                python=GeneratedProblemLanguage(
                    starter_code="pass",
                    reference_solution="pass",
                    function_signature=FunctionSignature(
                        name="f", params=[], return_type="int"
                    ),
                )
            ),
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
            languages=GeneratedProblemLanguages(
                python=GeneratedProblemLanguage(
                    starter_code="pass",
                    reference_solution="pass",
                    function_signature=FunctionSignature(
                        name="f", params=[], return_type="int"
                    ),
                )
            ),
        )


# ── GeneratedTestCase ──


def test_generated_test_case():
    """Test creating a test case with explicit value types."""
    tc = GeneratedTestCase(input=[[2, 7, 11, 15], 9], expected=[0, 1])
    assert tc.input == [[2, 7, 11, 15], 9]
    assert tc.expected == [0, 1]


def test_generated_test_case_primitives():
    """Test test case with various primitive types."""
    tc = GeneratedTestCase(input=["hello", 42, True, None], expected="world")
    assert tc.input == ["hello", 42, True, None]
    assert tc.expected == "world"


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


def test_verification_result_all_pass():
    """Test verification result when all checks pass."""
    result = VerificationResult(
        title_correct=True,
        leetcode_no_correct=True,
        description_correct=True,
        solution_correct=True,
        signature_matches=True,
        starter_code_correct=True,
        constraints_correct=True,
        examples_correct=True,
        difficulty_correct=True,
        comparison_strategy_correct=True,
    )
    assert result.is_valid() is True
    assert result.error_details == ""


def test_verification_result_with_failures():
    """Test verification result with failed checks."""
    result = VerificationResult(
        title_correct=True,
        leetcode_no_correct=False,
        description_correct=True,
        solution_correct=True,
        signature_matches=True,
        starter_code_correct=True,
        constraints_correct=True,
        examples_correct=False,
        difficulty_correct=True,
        comparison_strategy_correct=True,
        error_details="leetcode_no should be 58 not 59. Example 2 output is wrong.",
    )
    assert result.is_valid() is False
    summary = result.failed_checks_summary()
    assert "leetcode_no" in summary
    assert "examples" in summary
    assert "leetcode_no should be 58" in summary


def test_verification_result_is_valid_derived():
    """Test that is_valid() is derived from boolean fields, not an LLM field."""
    # Even if the model were to hallucinate, is_valid() checks actual fields
    result = VerificationResult(
        title_correct=True,
        leetcode_no_correct=True,
        description_correct=True,
        solution_correct=False,  # One failure
        signature_matches=True,
        starter_code_correct=True,
        constraints_correct=True,
        examples_correct=True,
        difficulty_correct=True,
        comparison_strategy_correct=True,
    )
    assert result.is_valid() is False
    assert "solution" in result.failed_checks_summary()


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
