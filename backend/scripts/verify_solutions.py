#!/usr/bin/env python3
"""
Local verification script for problem solutions.

Usage:
    # Verify all problems
    uv run python scripts/verify_solutions.py

    # Verify specific problem file
    uv run python scripts/verify_solutions.py 017-coin-change.yaml

    # Verbose output (show all test cases)
    uv run python scripts/verify_solutions.py --verbose
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "problems"


def load_problem(filepath: Path) -> dict:
    """Load and parse a problem YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def execute_solution(reference_solution: str, function_name: str, test_input: list) -> Any:
    """Execute the reference solution against a single test case."""
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


def verify_problem(filepath: Path, verbose: bool = False) -> tuple[bool, int, int, list[str]]:
    """
    Verify a single problem's reference solution against all test cases.

    Returns:
        (all_passed, passed_count, total_count, error_messages)
    """
    data = load_problem(filepath)
    title = data.get("title", filepath.name)

    # Get Python solution details
    python_lang = data.get("languages", {}).get("python", {})
    reference_solution = python_lang.get("reference_solution", "")
    function_sig = python_lang.get("function_signature", {})
    function_name = function_sig.get("name", "")

    if not reference_solution or not function_name:
        return False, 0, 0, [f"Missing reference_solution or function_name"]

    test_cases = data.get("test_cases", [])
    if not test_cases:
        return False, 0, 0, [f"No test cases defined"]

    passed = 0
    total = len(test_cases)
    errors = []

    for i, tc in enumerate(test_cases, 1):
        test_input = tc.get("input", [])
        expected = tc.get("expected")

        try:
            result = execute_solution(reference_solution, function_name, test_input)

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


def main():
    parser = argparse.ArgumentParser(description="Verify problem solutions locally")
    parser.add_argument("file", nargs="?", help="Specific file to verify (optional)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all test results")
    args = parser.parse_args()

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

    print(f"Verifying {len(yaml_files)} problem(s)...\n")

    total_passed = 0
    total_failed = 0
    failed_problems = []

    for filepath in yaml_files:
        data = load_problem(filepath)
        title = data.get("title", filepath.stem)
        seq = data.get("sequence_number", "?")

        print(f"[{seq:03d}] {title}...", end=" ", flush=True)

        try:
            all_passed, passed, total, errors = verify_problem(filepath, args.verbose)

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
