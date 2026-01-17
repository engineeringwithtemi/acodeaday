#!/usr/bin/env python3
"""
Verification script for problem solutions.

Supports two execution modes:
- python: Local execution using Python's exec() (default, fast, Python only)
- judge0: Remote execution via Judge0 API (tests actual Judge0 integration, any language)

Usage:
    # Verify all problems (local Python mode - default)
    uv run python scripts/verify_solutions.py

    # Verify all problems using Judge0
    uv run python scripts/verify_solutions.py --mode judge0

    # Verify a specific language using Judge0 (useful when adding new language support)
    uv run python scripts/verify_solutions.py --mode judge0 --lang javascript

    # Verify specific problem file
    uv run python scripts/verify_solutions.py 017-coin-change.yaml

    # Verbose output (show all test cases)
    uv run python scripts/verify_solutions.py --verbose

    # Combine options
    uv run python scripts/verify_solutions.py --mode judge0 --lang python --verbose 001-two-sum.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Add parent directory to path for importing app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "problems"


def load_problem(filepath: Path) -> dict:
    """Load and parse a problem YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def execute_solution_local(reference_solution: str, function_name: str, test_input: list) -> Any:
    """Execute the reference solution locally using Python's exec()."""
    # Create a namespace for execution
    namespace = {"List": list, "Optional": type(None), "Dict": dict, "Set": set, "Tuple": tuple}

    # Add typing imports
    exec("from typing import List, Optional, Dict, Set, Tuple, Any", namespace)

    # Execute the solution code
    exec(reference_solution, namespace)

    # Get the Solution class and instantiate it
    solution_class = namespace["Solution"]
    solution = solution_class()

    # Get the function and call it
    func = getattr(solution, function_name)
    return func(*test_input)


def execute_solution_judge0(
    reference_solution: str,
    function_name: str,
    test_cases: list[dict],
    language: str = "python",
) -> list[dict]:
    """
    Execute the reference solution via Judge0 API.

    Args:
        reference_solution: The solution code to execute
        function_name: Name of the function to call
        test_cases: List of test case dicts with input/expected
        language: Programming language (must be in SUPPORTED_LANGUAGES)

    Returns:
        List of test results with passed/failed status.
    """
    from app.services.judge0 import get_judge0_service
    from app.services.wrapper import get_wrapper_for_language, parse_judge0_output

    # Get the appropriate wrapper generator for this language
    wrapper_fn = get_wrapper_for_language(language)

    # Create mock TestCase objects for the wrapper
    class MockTestCase:
        def __init__(self, input_data, expected):
            self.input = input_data
            self.expected = expected

    mock_test_cases = [
        MockTestCase(tc.get("input", []), tc.get("expected"))
        for tc in test_cases
    ]

    # Generate wrapped code using the language-specific wrapper
    wrapped_code = wrapper_fn(
        user_code=reference_solution,
        test_cases=mock_test_cases,
        function_name=function_name,
        early_exit=False,
    )

    # Execute via Judge0
    judge0 = get_judge0_service()
    result = judge0.execute_code(
        source_code=wrapped_code,
        language=language,
    )

    # Check for compilation/runtime errors
    status_id = result.get("status", {}).get("id")
    if status_id != 3:  # 3 = Accepted
        status_desc = result.get("status", {}).get("description", "Unknown")
        stderr = result.get("stderr", "")
        compile_output = result.get("compile_output", "")
        error_msg = stderr or compile_output or status_desc
        raise RuntimeError(f"Judge0 execution failed: {error_msg}")

    # Parse the JSON output
    stdout = result.get("stdout", "")
    if not stdout:
        raise RuntimeError("Judge0 returned no output")

    return parse_judge0_output(stdout)


def verify_problem_local(filepath: Path, verbose: bool = False) -> tuple[bool, int, int, list[str]]:
    """
    Verify a single problem's reference solution using local Python execution.

    Returns:
        (all_passed, passed_count, total_count, error_messages)
    """
    data = load_problem(filepath)

    # Get Python solution details
    python_lang = data.get("languages", {}).get("python", {})
    reference_solution = python_lang.get("reference_solution", "")
    function_sig = python_lang.get("function_signature", {})
    function_name = function_sig.get("name", "")

    if not reference_solution or not function_name:
        return False, 0, 0, ["Missing reference_solution or function_name"]

    test_cases = data.get("test_cases", [])
    if not test_cases:
        return False, 0, 0, ["No test cases defined"]

    passed = 0
    total = len(test_cases)
    errors = []

    for i, tc in enumerate(test_cases, 1):
        test_input = tc.get("input", [])
        expected = tc.get("expected")

        try:
            result = execute_solution_local(reference_solution, function_name, test_input)

            if result == expected:
                passed += 1
                if verbose:
                    print(f"    ✓ Test {i}: input={test_input} -> {result}")
            else:
                errors.append(f"Test {i}: expected {expected}, got {result} (input: {test_input})")
                if verbose:
                    print(f"    ✗ Test {i}: input={test_input}")
                    print(f"      Expected: {expected}")
                    print(f"      Got:      {result}")
        except Exception as e:
            errors.append(f"Test {i}: {type(e).__name__}: {e} (input: {test_input})")
            if verbose:
                print(f"    ✗ Test {i}: ERROR - {type(e).__name__}: {e}")

    return passed == total, passed, total, errors


def verify_problem_judge0(filepath: Path, language: str = "python", verbose: bool = False) -> tuple[bool, int, int, list[str]]:
    """
    Verify a single problem's reference solution using Judge0 API.

    Args:
        filepath: Path to the problem YAML file
        language: Programming language to verify (e.g., "python", "javascript")
        verbose: Show detailed output for each test case

    Returns:
        (all_passed, passed_count, total_count, error_messages)
    """
    data = load_problem(filepath)

    # Get language-specific solution details
    lang_config = data.get("languages", {}).get(language, {})
    if not lang_config:
        return False, 0, 0, [f"Language '{language}' not found in problem"]

    reference_solution = lang_config.get("reference_solution", "")
    function_sig = lang_config.get("function_signature", {})
    function_name = function_sig.get("name", "")

    if not reference_solution or not function_name:
        return False, 0, 0, [f"Missing reference_solution or function_name for '{language}'"]

    test_cases = data.get("test_cases", [])
    if not test_cases:
        return False, 0, 0, ["No test cases defined"]

    # Execute all test cases via Judge0 in a single request
    try:
        results = execute_solution_judge0(reference_solution, function_name, test_cases, language)
    except Exception as e:
        return False, 0, len(test_cases), [f"Judge0 error: {type(e).__name__}: {e}"]

    passed = 0
    total = len(results)
    errors = []

    for r in results:
        test_num = r.get("test_number", "?")
        test_passed = r.get("passed", False)
        test_input = r.get("input", [])
        output = r.get("output")
        expected = r.get("expected")
        error = r.get("error")

        if test_passed:
            passed += 1
            if verbose:
                print(f"    ✓ Test {test_num}: input={test_input} -> {output}")
        else:
            if error:
                errors.append(f"Test {test_num}: {r.get('error_type', 'Error')}: {error} (input: {test_input})")
                if verbose:
                    print(f"    ✗ Test {test_num}: ERROR - {error}")
            else:
                errors.append(f"Test {test_num}: expected {expected}, got {output} (input: {test_input})")
                if verbose:
                    print(f"    ✗ Test {test_num}: input={test_input}")
                    print(f"      Expected: {expected}")
                    print(f"      Got:      {output}")

    return passed == total, passed, total, errors


def verify_problem(filepath: Path, mode: str = "python", language: str = "python", verbose: bool = False) -> tuple[bool, int, int, list[str]]:
    """
    Verify a single problem's reference solution against all test cases.

    Args:
        filepath: Path to the problem YAML file
        mode: Execution mode - "python" (local exec, Python only) or "judge0" (remote, any language)
        language: Programming language to verify (only used with judge0 mode)
        verbose: Show detailed output for each test case

    Returns:
        (all_passed, passed_count, total_count, error_messages)
    """
    if mode == "judge0":
        return verify_problem_judge0(filepath, language, verbose)
    else:
        # Local mode only supports Python (uses exec())
        return verify_problem_local(filepath, verbose)


def main():
    parser = argparse.ArgumentParser(description="Verify problem solutions")
    parser.add_argument("file", nargs="?", help="Specific file to verify (optional)")
    parser.add_argument(
        "--mode", "-m",
        choices=["python", "judge0"],
        default="python",
        help="Execution mode: 'python' for local exec (default, Python only), 'judge0' for Judge0 API (any language)"
    )
    parser.add_argument(
        "--lang", "-l",
        default="python",
        help="Language to verify (default: python). Only used with --mode judge0. Examples: python, javascript"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all test results")
    args = parser.parse_args()

    # Warn if --lang is used without judge0 mode
    if args.lang != "python" and args.mode != "judge0":
        print(f"Warning: --lang '{args.lang}' is ignored in local Python mode. Use --mode judge0 for other languages.")
        args.lang = "python"

    if not DATA_DIR.exists():
        print(f"Error: Data directory not found: {DATA_DIR}")
        return 1

    if args.file:
        # Verify specific file
        filepath = DATA_DIR / args.file
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return 1
        yaml_files = [filepath]
    else:
        # Verify all files
        yaml_files = sorted(DATA_DIR.glob("*.yaml"))

    if not yaml_files:
        print("No problem files found.")
        return 0

    if args.mode == "judge0":
        mode_label = f"Judge0 ({args.lang})"
    else:
        mode_label = "local Python"
    print(f"Verifying {len(yaml_files)} problem(s) using {mode_label}...\n")

    total_passed = 0
    total_failed = 0
    failed_problems = []

    for filepath in yaml_files:
        data = load_problem(filepath)
        title = data.get("title", filepath.stem)
        seq = data.get("sequence_number", "?")

        print(f"[{seq:03d}] {title}...", end=" ", flush=True)

        try:
            all_passed, passed, total, errors = verify_problem(filepath, args.mode, args.lang, args.verbose)

            if all_passed:
                print(f"✓ ({passed}/{total} tests)")
                total_passed += 1
            else:
                print(f"✗ ({passed}/{total} tests)")
                total_failed += 1
                failed_problems.append((filepath.name, title, errors))
                if not args.verbose:
                    for err in errors[:3]:  # Show first 3 errors
                        print(f"    - {err}")
                    if len(errors) > 3:
                        print(f"    ... and {len(errors) - 3} more errors")
        except Exception as e:
            print(f"✗ (ERROR: {e})")
            total_failed += 1
            failed_problems.append((filepath.name, title, [str(e)]))

    print(f"\n{'='*60}")
    print(f"Results: {total_passed} passed, {total_failed} failed")

    if failed_problems:
        print(f"\nFailed problems:")
        for filename, title, _ in failed_problems:
            print(f"  - {filename}: {title}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
