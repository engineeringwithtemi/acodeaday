"""API routes for code execution (run and submit)."""

import json
import uuid

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
                test_number=result_data.get("test", i + 1),
                passed=result_data.get("passed", False),
                output=result_data.get("output"),
                expected=result_data.get("expected"),
                error=result_data.get("error"),
                error_type=result_data.get("error_type"),
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
    Run code against visible test cases only (not hidden).

    This is the "Run Code" button - shows only example test cases.
    """
    problem, problem_lang, test_cases = await _get_problem_with_details(
        db, request.problem_slug, request.language.value
    )

    # Filter to only visible test cases
    visible_test_cases = [tc for tc in test_cases if not tc.is_hidden]

    if not visible_test_cases:
        raise HTTPException(
            status_code=400, detail="No visible test cases found for this problem"
        )

    # Get function name from signature
    function_name = problem_lang.function_signature.get("name")
    if not function_name:
        raise HTTPException(
            status_code=500, detail="Problem configuration error: missing function name"
        )

    # Execute code
    execution_result = await _execute_code_with_wrapper(
        user_code=request.code,
        language=request.language.value,
        function_name=function_name,
        test_cases=visible_test_cases,
    )

    return RunCodeResponse(**execution_result)


@router.post("/submit", response_model=SubmitCodeResponse)
async def submit_code(
    request: SubmitCodeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit code against ALL test cases (including hidden).

    This is the "Submit" button - runs all tests and updates user progress.
    """
    user_id = user["id"]

    problem, problem_lang, test_cases = await _get_problem_with_details(
        db, request.problem_slug, request.language.value
    )

    if not test_cases:
        raise HTTPException(
            status_code=400, detail="No test cases found for this problem"
        )

    # Get function name from signature
    function_name = problem_lang.function_signature.get("name")
    if not function_name:
        raise HTTPException(
            status_code=500, detail="Problem configuration error: missing function name"
        )

    # Execute code against ALL test cases
    execution_result = await _execute_code_with_wrapper(
        user_code=request.code,
        language=request.language.value,
        function_name=function_name,
        test_cases=test_cases,
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
