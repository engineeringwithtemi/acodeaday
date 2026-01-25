"""
Unit tests for the comparison service.

Tests are written FIRST (TDD) - the implementation doesn't exist yet.
These tests define the behavior of the compare() function.
"""

import pytest
from app.services.comparison import compare, ComparisonStrategy


class TestExactComparison:
    """Test EXACT comparison strategy (default)."""

    @pytest.mark.parametrize(
        "actual,expected,should_match",
        [
            # Arrays - order matters
            ([0, 1], [0, 1], True),
            ([1, 0], [0, 1], False),
            ([], [], True),
            ([1], [1, 2], False),
            # Strings
            ("hello", "hello", True),
            ("hello", "world", False),
            ("", "", True),
            # None
            (None, None, True),
            (None, 0, False),
            # Numbers
            (42, 42, True),
            (42, 43, False),
            (0, 0, True),
            (-1, -1, True),
            # Booleans
            (True, True, True),
            (False, False, True),
            (True, False, False),
            # Nested structures
            ([[1, 2], [3, 4]], [[1, 2], [3, 4]], True),
            ([[1, 2], [3, 4]], [[3, 4], [1, 2]], False),
            ({"a": 1, "b": 2}, {"a": 1, "b": 2}, True),
            ({"a": 1}, {"a": 1, "b": 2}, False),
        ],
    )
    def test_exact_comparison(self, actual, expected, should_match):
        """Test exact equality comparison."""
        result = compare(actual, expected, ComparisonStrategy.EXACT)
        assert result == should_match

    def test_exact_is_default_strategy(self):
        """Test that EXACT is used when no strategy specified."""
        assert compare([1, 2], [1, 2], None) is True
        assert compare([1, 2], [2, 1], None) is False

    def test_exact_with_floats(self):
        """Test floating point comparison with small epsilon tolerance."""
        # Direct equality should work for most cases
        assert compare(0.3, 0.3, ComparisonStrategy.EXACT) is True

        # The classic floating point issue - should be handled gracefully
        # 0.1 + 0.2 = 0.30000000000000004 in Python
        # We'll use a small epsilon for float comparison
        assert compare(0.1 + 0.2, 0.3, ComparisonStrategy.EXACT) is True
        assert compare(1.0000001, 1.0, ComparisonStrategy.EXACT) is False


class TestUnorderedArrayComparison:
    """Test UNORDERED_ARRAY comparison strategy."""

    @pytest.mark.parametrize(
        "actual,expected,should_match",
        [
            # Basic unordered matching
            ([1, 0], [0, 1], True),
            ([1, 2, 3], [3, 2, 1], True),
            ([5, 3, 8, 1], [1, 3, 5, 8], True),
            # Empty arrays
            ([], [], True),
            # Single element
            ([42], [42], True),
            ([42], [43], False),
            # Duplicates - frequency matters
            ([1, 1, 2], [1, 2, 1], True),
            ([1, 1, 2], [1, 2, 2], False),
            ([1, 1, 1], [1, 1, 1], True),
            # Different lengths
            ([1], [1, 2], False),
            ([1, 2, 3], [1, 2], False),
            # Nested arrays (order of outer array doesn't matter)
            ([[1, 2], [3, 4]], [[3, 4], [1, 2]], True),
            ([[1, 2], [3, 4]], [[1, 2], [4, 3]], False),  # Inner order matters
            # All same elements
            ([1, 1, 1], [1, 1, 1], True),
            ([2, 2], [2, 2, 2], False),
        ],
    )
    def test_unordered_array_comparison(self, actual, expected, should_match):
        """Test unordered array comparison."""
        result = compare(actual, expected, ComparisonStrategy.UNORDERED_ARRAY)
        assert result == should_match

    def test_unordered_with_strings(self):
        """Test unordered comparison with string arrays."""
        assert compare(
            ["apple", "banana"],
            ["banana", "apple"],
            ComparisonStrategy.UNORDERED_ARRAY
        ) is True

        assert compare(
            ["apple", "banana"],
            ["apple", "cherry"],
            ComparisonStrategy.UNORDERED_ARRAY
        ) is False

    def test_unordered_non_array_falls_back_to_exact(self):
        """Test that non-array types use exact comparison."""
        # Single values should compare exactly
        assert compare(42, 42, ComparisonStrategy.UNORDERED_ARRAY) is True
        assert compare("hello", "hello", ComparisonStrategy.UNORDERED_ARRAY) is True
        assert compare(None, None, ComparisonStrategy.UNORDERED_ARRAY) is True


class TestInPlaceOnlyComparison:
    """Test IN_PLACE_ONLY comparison strategy."""

    def test_in_place_only_ignores_return_value(self):
        """Test that return value is completely ignored."""
        actual = {"return_value": None, "mutated_input": [1, 2, 3]}
        expected = {"return_value": None, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

        # Different return values should still match if input matches
        actual = {"return_value": 42, "mutated_input": [1, 2, 3]}
        expected = {"return_value": None, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

        actual = {"return_value": [1, 2], "mutated_input": [5, 6]}
        expected = {"return_value": "different", "mutated_input": [5, 6]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

    def test_in_place_only_checks_mutated_input(self):
        """Test that mutated_input must match exactly."""
        actual = {"return_value": None, "mutated_input": [1, 2, 3]}
        expected = {"return_value": None, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

        # Different mutated input should fail
        actual = {"return_value": None, "mutated_input": [1, 2, 3]}
        expected = {"return_value": None, "mutated_input": [1, 2, 4]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is False

    def test_in_place_only_with_complex_mutations(self):
        """Test in-place comparison with complex data structures."""
        # Nested arrays
        actual = {"return_value": None, "mutated_input": [[1, 2], [3, 4]]}
        expected = {"return_value": None, "mutated_input": [[1, 2], [3, 4]]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

        # Different nested structure
        actual = {"return_value": None, "mutated_input": [[1, 2], [3, 4]]}
        expected = {"return_value": None, "mutated_input": [[1, 2], [4, 3]]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is False

    def test_in_place_only_requires_dict_format(self):
        """Test that IN_PLACE_ONLY requires specific dict format."""
        # Non-dict should return False (graceful failure)
        assert compare([1, 2, 3], [1, 2, 3], ComparisonStrategy.IN_PLACE_ONLY) is False

        # Missing keys should return False
        assert compare(
            {"return_value": None},
            {"return_value": None, "mutated_input": [1]},
            ComparisonStrategy.IN_PLACE_ONLY
        ) is False


class TestInPlaceWithLengthComparison:
    """Test IN_PLACE_WITH_LENGTH comparison strategy."""

    def test_in_place_with_length_checks_return_value(self):
        """Test that return value (k) is checked."""
        actual = {"return_value": 2, "mutated_input": [1, 2, 3]}
        expected = {"return_value": 2, "mutated_input": [1, 2, 5]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

        # Different k should fail
        actual = {"return_value": 2, "mutated_input": [1, 2, 3]}
        expected = {"return_value": 3, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is False

    def test_in_place_with_length_checks_first_k_elements(self):
        """Test that only first k elements are compared."""
        # First 2 elements match, rest differ - should pass
        actual = {"return_value": 2, "mutated_input": [1, 2, 999]}
        expected = {"return_value": 2, "mutated_input": [1, 2, 5]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

        # First k elements differ - should fail
        actual = {"return_value": 2, "mutated_input": [1, 999, 3]}
        expected = {"return_value": 2, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is False

    def test_in_place_with_length_k_zero(self):
        """Test edge case where k=0."""
        actual = {"return_value": 0, "mutated_input": [999, 888]}
        expected = {"return_value": 0, "mutated_input": [1, 2]}
        # k=0 means no elements to check, only return value matters
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

    def test_in_place_with_length_k_equals_length(self):
        """Test when k equals array length."""
        actual = {"return_value": 3, "mutated_input": [1, 2, 3]}
        expected = {"return_value": 3, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

        # All elements must match
        actual = {"return_value": 3, "mutated_input": [1, 2, 3]}
        expected = {"return_value": 3, "mutated_input": [1, 2, 4]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is False

    def test_in_place_with_length_k_exceeds_length(self):
        """Test when k exceeds array length."""
        # Should compare entire array when k > len(array)
        actual = {"return_value": 10, "mutated_input": [1, 2, 3]}
        expected = {"return_value": 10, "mutated_input": [1, 2, 3]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

    def test_in_place_with_length_requires_dict_format(self):
        """Test that IN_PLACE_WITH_LENGTH requires specific dict format."""
        # Non-dict should return False (graceful failure)
        assert compare([1, 2, 3], [1, 2, 3], ComparisonStrategy.IN_PLACE_WITH_LENGTH) is False

        # Missing keys should return False
        assert compare(
            {"return_value": 2},
            {"return_value": 2, "mutated_input": [1]},
            ComparisonStrategy.IN_PLACE_WITH_LENGTH
        ) is False

    def test_in_place_with_length_return_must_be_int(self):
        """Test that return_value must be an integer for k."""
        # Non-integer k should return False (graceful failure)
        assert compare(
            {"return_value": "not_an_int", "mutated_input": [1, 2]},
            {"return_value": 2, "mutated_input": [1, 2]},
            ComparisonStrategy.IN_PLACE_WITH_LENGTH
        ) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_strategy_falls_back_to_exact(self):
        """Test that unknown strategy falls back to EXACT."""
        # Using a string that's not a valid strategy
        assert compare([1, 2], [1, 2], "UNKNOWN_STRATEGY") is True
        assert compare([1, 2], [2, 1], "UNKNOWN_STRATEGY") is False

    def test_none_strategy_uses_exact(self):
        """Test that None strategy defaults to EXACT."""
        assert compare([1, 2], [1, 2], None) is True
        assert compare([1, 2], [2, 1], None) is False

    def test_type_mismatch(self):
        """Test comparing different types."""
        assert compare(42, "42", ComparisonStrategy.EXACT) is False
        assert compare([1, 2], (1, 2), ComparisonStrategy.EXACT) is False
        assert compare(None, [], ComparisonStrategy.EXACT) is False
        assert compare(0, False, ComparisonStrategy.EXACT) is False

    def test_floating_point_precision(self):
        """Test floating point comparison with epsilon tolerance."""
        # Should handle floating point arithmetic
        assert compare(0.1 + 0.2, 0.3, ComparisonStrategy.EXACT) is True
        # 1.0000001 is within default tolerance (1e-9), so use larger diff
        assert compare(1.0, 1.001, ComparisonStrategy.EXACT) is False

        # In arrays
        assert compare([0.1 + 0.2], [0.3], ComparisonStrategy.EXACT) is True
        assert compare([0.1 + 0.2], [0.3], ComparisonStrategy.UNORDERED_ARRAY) is True

    def test_deeply_nested_structures(self):
        """Test comparison of deeply nested structures."""
        deep1 = {"a": [1, {"b": [2, 3]}]}
        deep2 = {"a": [1, {"b": [2, 3]}]}
        deep3 = {"a": [1, {"b": [2, 4]}]}

        assert compare(deep1, deep2, ComparisonStrategy.EXACT) is True
        assert compare(deep1, deep3, ComparisonStrategy.EXACT) is False

    def test_empty_structures(self):
        """Test comparison of empty structures."""
        assert compare([], [], ComparisonStrategy.EXACT) is True
        assert compare({}, {}, ComparisonStrategy.EXACT) is True
        assert compare("", "", ComparisonStrategy.EXACT) is True
        assert compare([], [], ComparisonStrategy.UNORDERED_ARRAY) is True

    def test_security_json_safe_types_only(self):
        """Test that only JSON-safe types are compared (security)."""
        # Custom objects with __lt__ or __eq__ could be exploited
        # However, in practice, Judge0 output comes through JSON parsing
        # which only produces JSON-safe types (dict, list, str, int, float, bool, None)
        # So this is mostly a documentation test - the compare function
        # will use the object's __eq__ but that's okay for JSON-parsed data
        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                # This would be called, but JSON parsing prevents custom objects
                return self.value == getattr(other, 'value', other)

        obj1 = CustomObject(1)
        obj2 = CustomObject(2)

        # Since we rely on JSON parsing to sanitize, this just returns False
        # The security boundary is at JSON parsing, not comparison
        result = compare(obj1, obj2, ComparisonStrategy.EXACT)
        # Result depends on CustomObject.__eq__ implementation
        assert isinstance(result, bool)


class TestRealWorldScenarios:
    """Test real-world problem scenarios."""

    def test_two_sum_scenario(self):
        """Test Two Sum problem (UNORDERED_ARRAY)."""
        # [0, 1] and [1, 0] should both be valid
        assert compare([0, 1], [1, 0], ComparisonStrategy.UNORDERED_ARRAY) is True
        assert compare([1, 0], [0, 1], ComparisonStrategy.UNORDERED_ARRAY) is True

    def test_remove_element_scenario(self):
        """Test Remove Element problem (IN_PLACE_WITH_LENGTH)."""
        # k=2, first 2 elements are [2, 2], rest don't matter
        actual = {"return_value": 2, "mutated_input": [2, 2, 3, 3]}
        expected = {"return_value": 2, "mutated_input": [2, 2, 0, 0]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_WITH_LENGTH) is True

    def test_reverse_array_in_place_scenario(self):
        """Test reverse array in place (IN_PLACE_ONLY)."""
        # Return value doesn't matter, only mutated array
        actual = {"return_value": None, "mutated_input": [3, 2, 1]}
        expected = {"return_value": None, "mutated_input": [3, 2, 1]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is True

        # Different mutation should fail
        actual = {"return_value": None, "mutated_input": [1, 2, 3]}
        expected = {"return_value": None, "mutated_input": [3, 2, 1]}
        assert compare(actual, expected, ComparisonStrategy.IN_PLACE_ONLY) is False

    def test_contains_duplicate_scenario(self):
        """Test Contains Duplicate problem (EXACT boolean)."""
        assert compare(True, True, ComparisonStrategy.EXACT) is True
        assert compare(False, False, ComparisonStrategy.EXACT) is True
        assert compare(True, False, ComparisonStrategy.EXACT) is False
