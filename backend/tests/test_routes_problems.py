"""Tests for problems routes."""

import pytest
from httpx import AsyncClient

from app.db.tables import Problem


@pytest.mark.asyncio
async def test_get_problems_empty(client: AsyncClient):
    """Test getting problems when database is empty."""
    response = await client.get("/api/problems/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_problems(client: AsyncClient, sample_problem: Problem):
    """Test getting list of problems."""
    response = await client.get("/api/problems/")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "two-sum"
    assert data[0]["title"] == "Two Sum"
    assert data[0]["difficulty"] == "easy"
    assert data[0]["sequence_number"] == 1


@pytest.mark.asyncio
async def test_get_problem_by_slug(client: AsyncClient, sample_problem: Problem):
    """Test getting problem details by slug."""
    response = await client.get("/api/problems/two-sum")
    assert response.status_code == 200

    data = response.json()
    assert data["slug"] == "two-sum"
    assert data["title"] == "Two Sum"
    assert data["description"] == "Find two numbers that add up to target"

    # Check languages
    assert len(data["languages"]) == 1
    assert data["languages"][0]["language"] == "python"

    # Check test cases
    assert len(data["test_cases"]) == 2


@pytest.mark.asyncio
async def test_get_problem_not_found(client: AsyncClient):
    """Test getting non-existent problem."""
    response = await client.get("/api/problems/nonexistent-problem")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
