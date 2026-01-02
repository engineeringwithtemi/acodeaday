"""Code wrapper generator for Judge0 execution."""

import json
from typing import Any

from app.config.logging import get_logger
from app.db.tables import TestCase

logger = get_logger(__name__)


def generate_python_wrapper(
    user_code: str,
    test_cases: list[TestCase],
    function_name: str,
) -> str:
    """
    Generate Python wrapper code for Judge0 execution.

    Takes user's Solution class code and wraps it with test harness that:
    1. Imports the user's code
    2. Instantiates Solution class for each test case
    3. Calls the function with test inputs
    4. Compares output with expected result
    5. Outputs JSON results to stdout

    Args:
        user_code: User's submitted code (includes class Solution)
        test_cases: List of TestCase objects with input/expected
        function_name: Name of the function to call (from function_signature)

    Returns:
        Complete Python code ready for Judge0 execution

    Example:
        user_code = '''
        class Solution:
            def twoSum(self, nums, target):
                return [0, 1]
        '''
        test_cases = [TestCase(input=[[2,7,11,15], 9], expected=[0,1])]
        wrapper = generate_python_wrapper(user_code, test_cases, "twoSum")

        # Generated code:
        # <user_code>
        #
        # if __name__ == "__main__":
        #     test_cases = [...json...]
        #     results = []
        #     for i, test in enumerate(test_cases):
        #         solution = Solution()
        #         result = solution.twoSum(*test["input"])
        #         results.append({"test": i+1, "passed": result == test["expected"], ...})
        #     print(json.dumps(results))
    """
    # Serialize test cases to JSON (convert SQLAlchemy objects to dicts)
    test_cases_json = [
        {
            "input": tc.input if isinstance(tc.input, list) else [tc.input],
            "expected": tc.expected,
            "is_hidden": tc.is_hidden,
        }
        for tc in test_cases
    ]

    wrapper = f'''{user_code}

import json
import sys

if __name__ == "__main__":
    test_cases = {json.dumps(test_cases_json)}
    results = []

    for i, test in enumerate(test_cases):
        try:
            # Create new Solution instance for each test
            solution = Solution()

            # Call user's function with test inputs
            # test["input"] is a list of arguments, so unpack with *
            result = solution.{function_name}(*test["input"])

            # Check if result matches expected
            passed = result == test["expected"]

            results.append({{
                "test_number": i + 1,
                "passed": passed,
                "output": result,
                "expected": test["expected"],
                "is_hidden": test["is_hidden"]
            }})

        except Exception as e:
            # Catch runtime errors in user code
            results.append({{
                "test_number": i + 1,
                "passed": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "expected": test["expected"],
                "is_hidden": test["is_hidden"]
            }})

    # Output results as JSON to stdout
    print(json.dumps(results))
'''

    return wrapper


def parse_judge0_output(stdout: str) -> list[dict[str, Any]]:
    """
    Parse Judge0 stdout containing test results JSON.

    Args:
        stdout: Output from Judge0 execution (should be JSON)

    Returns:
        List of test results

    Example:
        stdout = '[{"test_number": 1, "passed": true, "output": [0,1]}]'
        results = parse_judge0_output(stdout)
        # Returns: [{"test_number": 1, "passed": True, "output": [0,1]}]
    """
    try:
        # Judge0 output might have extra whitespace/newlines
        cleaned = stdout.strip()
        results = json.loads(cleaned)

        if not isinstance(results, list):
            logger.error("judge0_output_not_list", output=stdout)
            raise ValueError("Expected list of test results")

        return results

    except json.JSONDecodeError as e:
        logger.error("judge0_output_parse_error", error=str(e), output=stdout)
        raise ValueError(f"Could not parse Judge0 output as JSON: {e}")


def filter_hidden_tests(
    results: list[dict[str, Any]], show_hidden: bool = False
) -> list[dict[str, Any]]:
    """
    Filter out hidden test cases from results.

    Used for "Run Code" endpoint where we don't show hidden tests.
    For "Submit" endpoint, show_hidden=True to reveal all failures.

    Args:
        results: List of test results from parse_judge0_output()
        show_hidden: Whether to include hidden test results

    Returns:
        Filtered list of test results

    Example:
        results = [
            {"test_number": 1, "passed": True, "is_hidden": False},
            {"test_number": 2, "passed": False, "is_hidden": True}
        ]

        # For "Run Code" - hide test 2:
        filter_hidden_tests(results, show_hidden=False)
        # Returns: [{"test_number": 1, ...}]

        # For "Submit" - show all:
        filter_hidden_tests(results, show_hidden=True)
        # Returns: [both tests]
    """
    if show_hidden:
        return results

    return [r for r in results if not r.get("is_hidden", False)]


def get_execution_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate summary statistics from test results.

    Args:
        results: List of test results

    Returns:
        Summary dict with total, passed, failed counts

    Example:
        results = [
            {"passed": True},
            {"passed": False},
            {"passed": True}
        ]
        summary = get_execution_summary(results)
        # Returns: {
        #     "total": 3,
        #     "passed": 2,
        #     "failed": 1,
        #     "all_passed": False,
        #     "pass_rate": 0.6667
        # }
    """
    total = len(results)
    passed = sum(1 for r in results if r.get("passed", False))
    failed = total - passed

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "all_passed": passed == total,
        "pass_rate": passed / total if total > 0 else 0.0,
    }
