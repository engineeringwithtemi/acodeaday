"""Comparison strategies for test result validation."""

import math
from typing import Any

from app.db.tables import ComparisonStrategy


def _is_json_safe_type(obj: Any) -> bool:
    """Check if object is a JSON-safe type that can be sorted."""
    return isinstance(obj, (list, dict, str, int, float, bool, type(None)))


def _normalize_for_comparison(obj: Any, depth: int = 0) -> Any:
    """
    Normalize an object for unordered comparison.

    Only the TOP-LEVEL list is sorted. Inner lists maintain their order.
    This matches the expected behavior: [1, 0] == [0, 1] for Two Sum,
    but [[1, 2], [3, 4]] != [[1, 2], [4, 3]] (inner order matters).
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    if isinstance(obj, dict):
        # Sort dict by keys, but don't sort inner lists
        return tuple(sorted((k, _normalize_for_comparison(v, depth + 1)) for k, v in obj.items()))

    if isinstance(obj, list):
        if depth == 0:
            # Only sort at top level
            # Convert inner elements to tuples for comparison (without sorting them)
            normalized = [_to_comparable(item) for item in obj]
            try:
                return tuple(sorted(normalized))
            except TypeError:
                return tuple(normalized)
        else:
            # Inner lists: convert to tuple but don't sort
            return tuple(_normalize_for_comparison(item, depth + 1) for item in obj)

    # For other types, return as-is
    return obj


def _to_comparable(obj: Any) -> Any:
    """Convert object to a comparable form (tuple) without sorting inner lists."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    if isinstance(obj, dict):
        return tuple(sorted((k, _to_comparable(v)) for k, v in obj.items()))

    if isinstance(obj, list):
        # Convert to tuple but maintain order
        return tuple(_to_comparable(item) for item in obj)

    return obj


def _floats_equal(a: Any, b: Any, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> bool:
    """
    Compare two values with float tolerance.

    Handles nested structures containing floats.
    """
    if type(a) is not type(b):
        return False

    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

    if isinstance(a, (int, str, bool, type(None))):
        return a == b

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_floats_equal(x, y, rel_tol, abs_tol) for x, y in zip(a, b))

    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_floats_equal(a[k], b[k], rel_tol, abs_tol) for k in a.keys())

    return a == b


def _exact_compare(output: Any, expected: Any) -> bool:
    """Exact comparison with float tolerance."""
    return _floats_equal(output, expected)


def _unordered_array_compare(output: Any, expected: Any) -> bool:
    """
    Compare arrays ignoring order (deep comparison).

    Works with nested structures. Both arrays must contain the same elements
    in any order.
    """
    if not isinstance(output, list) or not isinstance(expected, list):
        return _exact_compare(output, expected)

    if len(output) != len(expected):
        return False

    # For float tolerance, we need a different approach than sorting
    # Sort indices by a normalized key, then compare pairwise with float tolerance
    try:
        # Try to sort both arrays and compare pairwise with float tolerance
        sorted_output = sorted(output, key=lambda x: _to_comparable(x))
        sorted_expected = sorted(expected, key=lambda x: _to_comparable(x))
        return _floats_equal(sorted_output, sorted_expected)
    except TypeError:
        # If sorting fails, fall back to normalized comparison
        normalized_output = _normalize_for_comparison(output)
        normalized_expected = _normalize_for_comparison(expected)
        return normalized_output == normalized_expected


def _in_place_only_compare(output: Any, expected: Any) -> bool:
    """
    Compare only the mutated input array (ignore return value).

    Expected format:
    {
        "mutated_input": [...],  # The modified input array
        "return_value": ...       # Ignored
    }

    Output format: same as expected
    """
    if not isinstance(output, dict) or not isinstance(expected, dict):
        return False

    if "mutated_input" not in output or "mutated_input" not in expected:
        return False

    return _exact_compare(output["mutated_input"], expected["mutated_input"])


def _in_place_with_length_compare(output: Any, expected: Any) -> bool:
    """
    Compare return value (k) and first k elements of mutated input.

    Expected format:
    {
        "mutated_input": [...],  # The modified input array
        "return_value": k         # Number of valid elements
    }

    Compares:
    1. return_value must match
    2. First k elements of mutated_input must match
    """
    if not isinstance(output, dict) or not isinstance(expected, dict):
        return False

    if "mutated_input" not in output or "mutated_input" not in expected:
        return False

    if "return_value" not in output or "return_value" not in expected:
        return False

    # Compare return values
    k_output = output["return_value"]
    k_expected = expected["return_value"]

    if not _exact_compare(k_output, k_expected):
        return False

    # Compare first k elements of mutated arrays
    mutated_output = output["mutated_input"]
    mutated_expected = expected["mutated_input"]

    if not isinstance(mutated_output, list) or not isinstance(mutated_expected, list):
        return False

    if not isinstance(k_expected, int) or k_expected < 0:
        return False

    # Extract first k elements
    first_k_output = mutated_output[:k_expected]
    first_k_expected = mutated_expected[:k_expected]

    return _exact_compare(first_k_output, first_k_expected)


def compare(output: Any, expected: Any, strategy: str | None = None) -> bool:
    """
    Compare test output against expected value using specified strategy.

    Args:
        output: The actual output from user's code
        expected: The expected output from test case
        strategy: Comparison strategy (defaults to EXACT)

    Returns:
        True if output matches expected according to strategy

    Strategies:
        EXACT: Direct equality with float tolerance
        UNORDERED_ARRAY: Arrays must contain same elements in any order
        IN_PLACE_ONLY: Compare only mutated_input (ignore return_value)
        IN_PLACE_WITH_LENGTH: Compare return_value and first k elements of mutated_input
    """
    # Default to EXACT if no strategy specified
    if strategy is None or strategy == ComparisonStrategy.EXACT:
        return _exact_compare(output, expected)

    # Handle different strategies
    if strategy == ComparisonStrategy.UNORDERED_ARRAY:
        return _unordered_array_compare(output, expected)

    if strategy == ComparisonStrategy.IN_PLACE_ONLY:
        return _in_place_only_compare(output, expected)

    if strategy == ComparisonStrategy.IN_PLACE_WITH_LENGTH:
        return _in_place_with_length_compare(output, expected)

    # Unknown strategy - fall back to exact comparison
    return _exact_compare(output, expected)
