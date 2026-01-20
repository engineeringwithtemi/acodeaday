"""Tests for code wrapper generation."""

import json

from app.services.wrapper import generate_python_wrapper


class _MockTestCase:
    def __init__(self, input_data, expected, comparison=None):
        self.input = input_data
        self.expected = expected
        self.comparison = comparison


def test_generate_python_wrapper_unordered_array(capsys):
    user_code = """
class Solution:
    def twoSum(self, nums, target):
        return [1, 0]
"""
    test_cases = [
        _MockTestCase([[2, 7, 11, 15], 9], [0, 1], comparison="unordered_array"),
    ]
    wrapper_code = generate_python_wrapper(user_code, test_cases, "twoSum")

    exec_globals = {"__name__": "__main__"}
    exec(wrapper_code, exec_globals)

    output = capsys.readouterr().out.strip()
    results = json.loads(output)

    assert results[0]["passed"] is True
