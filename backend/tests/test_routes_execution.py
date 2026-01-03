"""Tests for execution routes.

Note: These tests mock Judge0 service since it requires external service.
For integration tests with actual Judge0, see test_judge0_integration.py
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.db.tables import Problem


@pytest.mark.asyncio
async def test_run_code_not_found(client: AsyncClient):
    """Test running code for non-existent problem."""
    response = await client.post(
        "/api/run",
        json={
            "problem_slug": "nonexistent",
            "code": "class Solution:\n    pass",
            "language": "python",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@patch("app.routes.execution.get_judge0_service")
async def test_run_code_success(
    mock_judge0_service,
    client: AsyncClient,
    sample_problem: Problem,
):
    """Test successful code execution (mocked Judge0)."""
    # Mock Judge0 response (execute_code is synchronous)
    mock_service = MagicMock()
    mock_service.execute_code.return_value = {
        "stdout": '[{"test": 1, "passed": true, "output": [0, 1], "expected": [0, 1], "error": null}]',
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }
    mock_judge0_service.return_value = mock_service

    response = await client.post(
        "/api/run",
        json={
            "problem_slug": "two-sum",
            "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
            "language": "python",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["results"]) == 1  # Only non-hidden test cases
    assert data["results"][0]["passed"] is True
    assert data["summary"]["total"] == 1
    assert data["summary"]["passed"] == 1


@pytest.mark.asyncio
@patch("app.routes.execution.get_judge0_service")
async def test_submit_code_success(
    mock_judge0_service,
    client: AsyncClient,
    auth_headers: dict,
    sample_problem: Problem,
):
    """Test successful code submission (mocked Judge0)."""
    # Mock Judge0 response (all tests passed, execute_code is synchronous)
    mock_service = MagicMock()
    mock_service.execute_code.return_value = {
        "stdout": '[{"test": 1, "passed": true, "output": [0, 1], "expected": [0, 1], "error": null}, '
        '{"test": 2, "passed": true, "output": [1, 2], "expected": [1, 2], "error": null}]',
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }
    mock_judge0_service.return_value = mock_service

    response = await client.post(
        "/api/submit",
        json={
            "problem_slug": "two-sum",
            "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
            "language": "python",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["results"]) == 2  # All test cases (including hidden)
    assert data["summary"]["passed"] == 2
    assert data["submission_id"] is not None

    # Check progress update
    assert data["times_solved"] == 1
    assert data["is_mastered"] is False
    assert data["next_review_date"] is not None


@pytest.mark.asyncio
@patch("app.routes.execution.get_judge0_service")
async def test_submit_code_failed(
    mock_judge0_service,
    client: AsyncClient,
    auth_headers: dict,
    sample_problem: Problem,
):
    """Test failed code submission (mocked Judge0)."""
    # Mock Judge0 response (test failed, execute_code is synchronous)
    mock_service = MagicMock()
    mock_service.execute_code.return_value = {
        "stdout": '[{"test": 1, "passed": false, "output": [0, 0], "expected": [0, 1], "error": null}, '
        '{"test": 2, "passed": true, "output": [1, 2], "expected": [1, 2], "error": null}]',
        "stderr": "",
        "status": {"id": 3, "description": "Accepted"},
    }
    mock_judge0_service.return_value = mock_service

    response = await client.post(
        "/api/submit",
        json={
            "problem_slug": "two-sum",
            "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 0]",
            "language": "python",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is False
    assert data["summary"]["passed"] == 1
    assert data["summary"]["failed"] == 1

    # No progress update on failed submission
    assert data["times_solved"] is None
    assert data["is_mastered"] is None


@pytest.mark.asyncio
async def test_submit_unauthorized(client: AsyncClient, sample_problem: Problem):
    """Test submitting without authentication."""
    response = await client.post(
        "/api/submit",
        json={
            "problem_slug": "two-sum",
            "code": "class Solution:\n    pass",
            "language": "python",
        },
    )
    assert response.status_code == 401
