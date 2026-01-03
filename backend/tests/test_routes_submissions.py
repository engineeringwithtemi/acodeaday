"""Tests for submissions routes."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import (
    Difficulty,
    Language,
    Problem,
    Submission,
)


@pytest.mark.asyncio
async def test_get_submissions_empty(
    client: AsyncClient, auth_headers: dict, test_db: AsyncSession
):
    """Test getting submissions when none exist."""
    # Create a problem with no submissions
    problem = Problem(
        id=uuid.uuid4(),
        title="Problem",
        slug="problem",
        description="Test",
        difficulty=Difficulty.EASY,
        pattern="array",
        sequence_number=1,
        constraints=[],
        examples={"examples": []},
    )
    test_db.add(problem)
    await test_db.commit()

    response = await client.get(
        f"/api/submissions/{problem.id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_submissions(
    client: AsyncClient,
    auth_headers: dict,
    problem_with_submissions: tuple[Problem, list[Submission]],
):
    """Test getting submission history for a problem."""
    problem, submissions = problem_with_submissions

    response = await client.get(
        f"/api/submissions/{problem.id}", headers=auth_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    # Check first submission (most recent)
    assert data[0]["problem_title"] == "Two Sum"
    assert data[0]["language"] == "python"
    assert data[0]["passed"] in [True, False]
    assert "code" in data[0]


@pytest.mark.asyncio
async def test_get_submissions_unauthorized(
    client: AsyncClient, problem_with_submissions: tuple[Problem, list[Submission]]
):
    """Test getting submissions without authentication."""
    problem, _ = problem_with_submissions

    response = await client.get(f"/api/submissions/{problem.id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_submissions_other_user(
    client: AsyncClient, auth_headers: dict, test_db: AsyncSession
):
    """Test that users can only see their own submissions."""
    # Create problem
    problem = Problem(
        id=uuid.uuid4(),
        title="Problem",
        slug="problem",
        description="Test",
        difficulty=Difficulty.EASY,
        pattern="array",
        sequence_number=1,
        constraints=[],
        examples={"examples": []},
    )
    test_db.add(problem)
    await test_db.flush()

    # Create submission by different user
    other_submission = Submission(
        user_id="other_user",
        problem_id=problem.id,
        code="code",
        language=Language.PYTHON,
        passed=True,
    )
    test_db.add(other_submission)
    await test_db.commit()

    # Current user (admin) should not see other user's submissions
    response = await client.get(
        f"/api/submissions/{problem.id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 0
