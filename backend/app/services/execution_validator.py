"""Shared execution validation logic for Judge0 results.

Extracted from routes/execution.py so both the submission route and the
import workflow can use the same parse-and-compare logic.
"""

import asyncio
import json
from typing import Any

from app.config.logging import get_logger
from app.services.comparison import compare
from app.services.judge0 import get_judge0_service
from app.services.wrapper import generate_python_wrapper

logger = get_logger(__name__)


def parse_execution_results(
    judge0_result: dict,
    test_count: int,
    comparison_strategy: str | None = None,
) -> dict[str, Any]:
    """
    Parse Judge0 execution results into a structured dict.

    Returns:
        Dict with keys: success, results (list of dicts), summary, runtime_ms, memory_kb,
        compile_error, runtime_error.
    """
    stdout = judge0_result.get("stdout", "")
    stderr = judge0_result.get("stderr", "")
    compile_output = judge0_result.get("compile_output", "")
    status = judge0_result.get("status", {})

    runtime_seconds = judge0_result.get("time")
    memory_kb = judge0_result.get("memory")

    runtime_ms = None
    if runtime_seconds:
        try:
            runtime_ms = int(float(runtime_seconds) * 1000)
        except (ValueError, TypeError):
            pass

    # Compilation error
    if status.get("id") == 6:
        return {
            "success": False,
            "compile_error": compile_output or stderr,
            "results": [],
            "summary": {"total": test_count, "passed": 0, "failed": test_count},
            "runtime_ms": runtime_ms,
            "memory_kb": memory_kb,
        }

    # Runtime error / TLE / MLE
    if status.get("id") in [11, 12, 13]:
        return {
            "success": False,
            "runtime_error": stderr or status.get("description"),
            "results": [],
            "summary": {"total": test_count, "passed": 0, "failed": test_count},
            "runtime_ms": runtime_ms,
            "memory_kb": memory_kb,
        }

    # Parse JSON from stdout
    try:
        results_data = json.loads(stdout) if stdout else []
    except json.JSONDecodeError:
        return {
            "success": False,
            "runtime_error": f"Failed to parse test results. Output: {stdout[:200]}",
            "results": [],
            "summary": {"total": test_count, "passed": 0, "failed": test_count},
            "runtime_ms": runtime_ms,
            "memory_kb": memory_kb,
        }

    # Apply comparison strategy to each result
    test_results = []
    for i, result_data in enumerate(results_data):
        has_error = result_data.get("error") is not None
        passed = False

        if not has_error:
            output = result_data.get("output")
            expected = result_data.get("expected")
            passed = compare(output, expected, comparison_strategy)

        test_results.append({
            "test_number": result_data.get("test_number", i + 1),
            "passed": passed,
            "input": result_data.get("input"),
            "output": result_data.get("output"),
            "expected": result_data.get("expected"),
            "error": result_data.get("error"),
            "error_type": result_data.get("error_type"),
            "stdout": result_data.get("stdout"),
        })

    passed_count = sum(1 for r in test_results if r["passed"])
    all_passed = passed_count == len(test_results) and len(test_results) > 0

    return {
        "success": all_passed,
        "results": test_results,
        "summary": {
            "total": len(test_results),
            "passed": passed_count,
            "failed": len(test_results) - passed_count,
        },
        "runtime_ms": runtime_ms,
        "memory_kb": memory_kb,
    }


class _MockTestCase:
    """Lightweight test case object compatible with generate_python_wrapper."""

    def __init__(self, input_data: list[Any], expected: Any):
        self.input = input_data
        self.expected = expected


async def validate_solution_with_judge0(
    reference_solution: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    comparison_strategy: str | None = None,
) -> dict[str, Any]:
    """
    Run a reference solution against test cases via Judge0.

    Uses asyncio.to_thread() to avoid blocking the event loop with the
    synchronous Judge0 client.

    Args:
        reference_solution: Python code with class Solution
        function_name: Method name to call
        test_cases: List of {"input": [...], "expected": ...}
        comparison_strategy: Comparison strategy for results

    Returns:
        Dict with: all_passed, total, passed, failures
    """
    mock_cases = [
        _MockTestCase(input_data=tc["input"], expected=tc["expected"])
        for tc in test_cases
    ]

    wrapped_code = generate_python_wrapper(
        reference_solution, mock_cases, function_name
    )

    judge0 = get_judge0_service()

    # Run synchronous Judge0 call in a thread to avoid blocking
    judge0_result = await asyncio.to_thread(
        judge0.execute_code,
        source_code=wrapped_code,
        language="python",
    )

    parsed = parse_execution_results(
        judge0_result, len(test_cases), comparison_strategy
    )

    failures = []
    if not parsed["success"]:
        if parsed.get("compile_error"):
            failures.append({"error": f"Compile error: {parsed['compile_error']}"})
        elif parsed.get("runtime_error"):
            failures.append({"error": f"Runtime error: {parsed['runtime_error']}"})
        else:
            for r in parsed["results"]:
                if not r["passed"]:
                    failures.append({
                        "test_number": r["test_number"],
                        "input": r["input"],
                        "expected": r["expected"],
                        "actual": r["output"],
                        "error": r.get("error"),
                    })

    return {
        "all_passed": parsed["success"],
        "total": parsed["summary"]["total"],
        "passed": parsed["summary"]["passed"],
        "failures": failures,
    }
