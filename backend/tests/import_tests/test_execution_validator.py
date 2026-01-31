"""Tests for execution_validator shared logic."""

import json

import pytest

from app.services.execution_validator import parse_execution_results


# ── parse_execution_results ──


def test_parse_all_passed():
    """Test parsing results where all tests pass."""
    judge0_result = {
        "stdout": json.dumps([
            {"test_number": 1, "output": [0, 1], "expected": [0, 1], "input": [[2, 7], 9], "error": None},
            {"test_number": 2, "output": [1, 2], "expected": [1, 2], "input": [[3, 2, 4], 6], "error": None},
        ]),
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
        "time": "0.05",
        "memory": 1024,
    }

    result = parse_execution_results(judge0_result, 2)

    assert result["success"] is True
    assert result["summary"]["total"] == 2
    assert result["summary"]["passed"] == 2
    assert result["summary"]["failed"] == 0
    assert result["runtime_ms"] == 50
    assert result["memory_kb"] == 1024


def test_parse_some_failed():
    """Test parsing results where some tests fail."""
    judge0_result = {
        "stdout": json.dumps([
            {"test_number": 1, "output": [0, 1], "expected": [0, 1], "input": [[2, 7], 9], "error": None},
            {"test_number": 2, "output": [0, 0], "expected": [1, 2], "input": [[3, 2, 4], 6], "error": None},
        ]),
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }

    result = parse_execution_results(judge0_result, 2)

    assert result["success"] is False
    assert result["summary"]["passed"] == 1
    assert result["summary"]["failed"] == 1


def test_parse_compile_error():
    """Test parsing compilation error."""
    judge0_result = {
        "stdout": "",
        "stderr": "SyntaxError: invalid syntax",
        "compile_output": "SyntaxError: invalid syntax",
        "status": {"id": 6, "description": "Compilation Error"},
    }

    result = parse_execution_results(judge0_result, 3)

    assert result["success"] is False
    assert "SyntaxError" in result["compile_error"]
    assert result["summary"]["total"] == 3
    assert result["summary"]["failed"] == 3


def test_parse_runtime_error():
    """Test parsing runtime error (TLE/MLE)."""
    judge0_result = {
        "stdout": "",
        "stderr": "Time Limit Exceeded",
        "status": {"id": 11, "description": "Time Limit Exceeded"},
    }

    result = parse_execution_results(judge0_result, 2)

    assert result["success"] is False
    assert result["runtime_error"] == "Time Limit Exceeded"
    assert result["summary"]["failed"] == 2


def test_parse_invalid_json():
    """Test parsing invalid JSON in stdout."""
    judge0_result = {
        "stdout": "not valid json",
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }

    result = parse_execution_results(judge0_result, 1)

    assert result["success"] is False
    assert "Failed to parse" in result["runtime_error"]


def test_parse_empty_stdout():
    """Test parsing empty stdout."""
    judge0_result = {
        "stdout": "",
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }

    result = parse_execution_results(judge0_result, 1)

    assert result["success"] is False
    assert result["summary"]["total"] == 0


def test_parse_with_unordered_array():
    """Test parsing with unordered_array comparison strategy."""
    judge0_result = {
        "stdout": json.dumps([
            {"test_number": 1, "output": [1, 0], "expected": [0, 1], "input": [[2, 7], 9], "error": None},
        ]),
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }

    # Without strategy: should fail (order matters)
    result_exact = parse_execution_results(judge0_result, 1)
    assert result_exact["success"] is False

    # With unordered_array: should pass
    result_unordered = parse_execution_results(judge0_result, 1, "unordered_array")
    assert result_unordered["success"] is True


def test_parse_with_error_in_test():
    """Test parsing results that have errors in individual tests."""
    judge0_result = {
        "stdout": json.dumps([
            {"test_number": 1, "output": None, "expected": [0, 1], "input": [[2, 7], 9], "error": "ZeroDivisionError"},
        ]),
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }

    result = parse_execution_results(judge0_result, 1)

    assert result["success"] is False
    assert result["results"][0]["passed"] is False
    assert result["results"][0]["error"] == "ZeroDivisionError"


def test_parse_runtime_ms_conversion():
    """Test runtime conversion from seconds to milliseconds."""
    judge0_result = {
        "stdout": "[]",
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
        "time": "1.234",
    }

    result = parse_execution_results(judge0_result, 0)
    assert result["runtime_ms"] == 1234
