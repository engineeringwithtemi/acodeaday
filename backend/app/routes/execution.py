"""API routes for code execution (run and submit)."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config.logging import get_logger
from app.db.connection import get_db
from app.db.tables import Problem, ProblemLanguage, Submission, TestCase
from app.middleware.auth import get_current_user
from app.schemas.execution import (
    RunCodeRequest,
    RunCodeResponse,
    SubmitCodeRequest,
    SubmitCodeResponse,
    TestResult,
)
from app.services.judge0 import get_judge0_service
from app.services.progress import update_user_progress
from app.services.wrapper import generate_python_wrapper

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["execution"])


async def _get_problem_with_details(
    db: AsyncSession, slug: str, language: str
) -> tuple[Problem, ProblemLanguage, list[TestCase]]:
    """Helper to fetch problem with all related data."""
    result = await db.execute(
        select(Problem)
        .options(joinedload(Problem.languages), joinedload(Problem.test_cases))
        .where(Problem.slug == slug)
    )
    problem = result.unique().scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail=f"Problem '{slug}' not found")

    # Get language-specific data
    problem_lang = next(
        (lang for lang in problem.languages if lang.language.value == language), None
    )
    if not problem_lang:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{language}' not supported for this problem",
        )

    # Sort test cases by sequence
    test_cases = sorted(problem.test_cases, key=lambda tc: tc.sequence)

    return problem, problem_lang, test_cases


class _MockTestCase:
    """Mock TestCase object for custom inputs."""

    def __init__(self, input_data: list[Any], expected: Any = None):
        self.input = input_data
        self.expected = expected
        self.is_hidden = False


async def _execute_code_with_wrapper(
    user_code: str,
    language: str,
    function_name: str,
    test_cases: list[TestCase],
) -> dict:
    """Execute user code with wrapper and return parsed results."""
    judge0 = get_judge0_service()

    # Generate wrapper code
    if language == "python":
        wrapped_code = generate_python_wrapper(user_code, test_cases, function_name)
    else:
        raise HTTPException(
            status_code=400, detail=f"Language '{language}' not yet supported"
        )

    logger.info(
        "executing_code",
        language=language,
        function=function_name,
        test_count=len(test_cases),
    )

    # Execute on Judge0
    result = judge0.execute_code(source_code=wrapped_code, language=language)

    # Parse results from stdout
    return _parse_execution_results(result, test_cases)


def _parse_execution_results(judge0_result: dict, test_cases: list[TestCase]) -> dict:
    """Parse Judge0 execution results and return structured test results."""
    stdout = judge0_result.get("stdout", "")
    stderr = judge0_result.get("stderr", "")
    compile_output = judge0_result.get("compile_output", "")
    status = judge0_result.get("status", {})

    # Check for compilation errors
    if status.get("id") == 6:  # Compilation Error
        return {
            "success": False,
            "compile_error": compile_output or stderr,
            "results": [],
            "summary": {"total": len(test_cases), "passed": 0, "failed": len(test_cases)},
        }

    # Check for runtime errors (before JSON parsing)
    if status.get("id") in [11, 12, 13]:  # Runtime Error, Time Limit, etc.
        return {
            "success": False,
            "runtime_error": stderr or status.get("description"),
            "results": [],
            "summary": {"total": len(test_cases), "passed": 0, "failed": len(test_cases)},
        }

    # Try to parse JSON results from stdout
    try:
        results_data = json.loads(stdout) if stdout else []
    except json.JSONDecodeError:
        logger.error("failed_to_parse_stdout", stdout=stdout[:200])
        return {
            "success": False,
            "runtime_error": f"Failed to parse test results. Output: {stdout[:200]}",
            "results": [],
            "summary": {"total": len(test_cases), "passed": 0, "failed": len(test_cases)},
        }

    # Convert to TestResult schemas
    test_results = []
    for i, result_data in enumerate(results_data):
        test_results.append(
            TestResult(
                test_number=result_data.get("test_number", i + 1),
                passed=result_data.get("passed", False),
                input=result_data.get("input"),
                output=result_data.get("output"),
                expected=result_data.get("expected"),
                error=result_data.get("error"),
                error_type=result_data.get("error_type"),
                stdout=result_data.get("stdout"),
                is_hidden=test_cases[i].is_hidden if i < len(test_cases) else False,
            )
        )

    passed_count = sum(1 for r in test_results if r.passed)
    all_passed = passed_count == len(test_results)

    return {
        "success": all_passed,
        "results": test_results,
        "summary": {
            "total": len(test_results),
            "passed": passed_count,
            "failed": len(test_results) - passed_count,
        },
        "stdout": stdout if not all_passed else None,
        "stderr": stderr,
    }


@router.post("/run", response_model=RunCodeResponse)
async def run_code(
    request: RunCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run code against first 3 test cases or custom inputs.

    This is the "Run Code" button - shows first 3 test cases by sequence order,
    or runs against custom inputs if provided.
    """
    problem, problem_lang, test_cases = await _get_problem_with_details(
        db, request.problem_slug, request.language.value
    )

    # Get function name from signature
    function_name = problem_lang.function_signature.get("name")
    if not function_name:
        raise HTTPException(
            status_code=500, detail="Problem configuration error: missing function name"
        )

    # Handle custom input if provided
    if request.custom_input:
        logger.info(
            "running_custom_input",
            problem_slug=request.problem_slug,
            custom_test_count=len(request.custom_input),
        )

        # First, run reference solution to get expected outputs
        reference_code = problem_lang.reference_solution
        reference_test_cases = [
            _MockTestCase(input_data=inp, expected=None)
            for inp in request.custom_input
        ]

        reference_result = await _execute_code_with_wrapper(
            user_code=reference_code,
            language=request.language.value,
            function_name=function_name,
            test_cases=reference_test_cases,
        )

        # Check for actual errors (compile/runtime), not success
        # Success is based on output==expected, but expected is None for reference runs
        if reference_result.get("compile_error") or reference_result.get("runtime_error"):
            logger.error(
                "reference_solution_failed",
                problem_slug=request.problem_slug,
                error=reference_result.get("runtime_error") or reference_result.get("compile_error"),
            )
            raise HTTPException(
                status_code=500,
                detail="Reference solution failed to execute. Please check your custom inputs.",
            )

        # Check if any test case had an error
        results = reference_result.get("results", [])
        for r in results:
            if r.error:
                logger.error(
                    "reference_solution_test_error",
                    problem_slug=request.problem_slug,
                    error=r.error,
                    error_type=r.error_type,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Reference solution error: {r.error_type}: {r.error}",
                )

        # Get expected outputs from reference results
        expected_outputs = [r.output for r in reference_result["results"]]

        # Now run user code with expected outputs
        user_test_cases = [
            _MockTestCase(input_data=inp, expected=exp)
            for inp, exp in zip(request.custom_input, expected_outputs)
        ]

        execution_result = await _execute_code_with_wrapper(
            user_code=request.code,
            language=request.language.value,
            function_name=function_name,
            test_cases=user_test_cases,
        )

        return RunCodeResponse(**execution_result)

    # Use first 3 test cases from DB (default behavior)
    first_three_tests = test_cases[:3]

    if not first_three_tests:
        raise HTTPException(
            status_code=400, detail="No test cases found for this problem"
        )

    # Execute code
    execution_result = await _execute_code_with_wrapper(
        user_code=request.code,
        language=request.language.value,
        function_name=function_name,
        test_cases=first_three_tests,
    )

    return RunCodeResponse(**execution_result)


@router.post("/submit", response_model=SubmitCodeResponse)
async def submit_code(
    request: SubmitCodeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit code against first 3 test cases.

    This is the "Submit" button - runs first 3 tests and updates user progress.
    """
    user_id = user["id"]

    problem, problem_lang, test_cases = await _get_problem_with_details(
        db, request.problem_slug, request.language.value
    )

    # Always use first 3 test cases by sequence order
    first_three_tests = test_cases[:3]

    if not first_three_tests:
        raise HTTPException(
            status_code=400, detail="No test cases found for this problem"
        )

    # Get function name from signature
    function_name = problem_lang.function_signature.get("name")
    if not function_name:
        raise HTTPException(
            status_code=500, detail="Problem configuration error: missing function name"
        )

    # Execute code against first 3 test cases
    execution_result = await _execute_code_with_wrapper(
        user_code=request.code,
        language=request.language.value,
        function_name=function_name,
        test_cases=first_three_tests,
    )

    all_passed = execution_result["success"]

    # Create submission record
    submission = Submission(
        id=uuid.uuid4(),
        user_id=user_id,
        problem_id=problem.id,
        code=request.code,
        language=request.language,
        passed=all_passed,
        runtime_ms=None,  # TODO: Extract from Judge0 if needed
    )
    db.add(submission)

    # Update user progress if all tests passed
    progress_info = {}
    if all_passed:
        progress_info = await update_user_progress(
            db=db, user_id=user_id, problem_id=problem.id, passed=True
        )

    await db.commit()

    return SubmitCodeResponse(
        success=all_passed,
        results=execution_result["results"],
        summary=execution_result["summary"],
        submission_id=str(submission.id),
        runtime_ms=submission.runtime_ms,
        times_solved=progress_info.get("times_solved"),
        is_mastered=progress_info.get("is_mastered"),
        next_review_date=progress_info.get("next_review_date"),
    )
