"""Tests for progress routes."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import Problem, UserProgress


@pytest.mark.asyncio
async def test_get_today_empty(client: AsyncClient, auth_headers: dict):
    """Test getting today's session when no problems exist."""
    response = await client.get("/api/today", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["review_problems"] == []
    assert data["new_problem"] is None
    assert data["total_mastered"] == 0
    assert data["total_solved"] == 0


@pytest.mark.asyncio
async def test_get_today_with_progress(
    client: AsyncClient, auth_headers: dict, problems_with_progress: list[Problem]
):
    """Test getting today's session with progress."""
    response = await client.get("/api/today", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()

    # Should have 1 review problem (overdue)
    assert len(data["review_problems"]) == 1
    assert data["review_problems"][0]["slug"] == "problem-1"

    # Should have 1 new problem (problem-3)
    assert data["new_problem"] is not None
    assert data["new_problem"]["slug"] == "problem-3"

    # Stats
    assert data["total_mastered"] == 1
    assert data["total_solved"] == 2


@pytest.mark.asyncio
async def test_get_progress(
    client: AsyncClient, auth_headers: dict, problems_with_progress: list[Problem]
):
    """Test getting overall progress."""
    response = await client.get("/api/progress", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_problems"] == 3
    assert data["solved_count"] == 2
    assert data["mastered_count"] == 1
    assert data["in_progress_count"] == 1
    assert data["unsolved_count"] == 1
    assert data["due_for_review"] == 1

    # Breakdowns
    assert "easy" in data["problems_by_difficulty"]
    assert "array" in data["problems_by_pattern"]


@pytest.mark.asyncio
async def test_get_mastered(
    client: AsyncClient, auth_headers: dict, problems_with_progress: list[Problem]
):
    """Test getting mastered problems."""
    response = await client.get("/api/mastered", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "problem-2"
    assert data[0]["times_solved"] == 2
    assert data[0]["show_again"] is False


@pytest.mark.asyncio
async def test_show_again(
    client: AsyncClient,
    auth_headers: dict,
    problems_with_progress: list[Problem],
    test_db: AsyncSession,
    test_user_id: str,
):
    """Test marking a mastered problem to show again."""
    problem_id = problems_with_progress[1].id  # Problem 2 (mastered)

    response = await client.post(
        f"/api/mastered/{problem_id}/show-again", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify in database
    result = await test_db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == test_user_id)
        .where(UserProgress.problem_id == problem_id)
    )
    progress = result.scalar_one()

    assert progress.show_again is True
    assert progress.is_mastered is False
    assert progress.next_review_date == date.today()


@pytest.mark.asyncio
async def test_show_again_not_mastered(
    client: AsyncClient, auth_headers: dict, problems_with_progress: list[Problem]
):
    """Test marking a non-mastered problem to show again (should fail)."""
    problem_id = problems_with_progress[0].id  # Problem 1 (not mastered)

    response = await client.post(
        f"/api/mastered/{problem_id}/show-again", headers=auth_headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing protected endpoints without auth."""
    response = await client.get("/api/today")
    assert response.status_code == 401
