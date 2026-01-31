"""Tests for import API routes."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import Difficulty, ImportJob, ImportJobProblem, ImportJobStatus, Problem


@pytest.fixture
async def import_job(test_db: AsyncSession, test_user_id: str) -> ImportJob:
    """Create a sample import job."""
    job = ImportJob(
        id=uuid.uuid4(),
        user_id=test_user_id,
        prompt="Add 3 sliding window problems",
        status=ImportJobStatus.COMPLETED,
        message="Imported 3 of 3 problem(s)",
        progress=3,
        total=3,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
    return job


@pytest.fixture
async def import_job_with_problems(
    test_db: AsyncSession, test_user_id: str
) -> tuple[ImportJob, list[Problem]]:
    """Create import job linked to problems."""
    job = ImportJob(
        id=uuid.uuid4(),
        user_id=test_user_id,
        prompt="Add Two Sum",
        status=ImportJobStatus.COMPLETED,
        message="Imported 1 of 1 problem(s)",
        progress=1,
        total=1,
    )
    test_db.add(job)
    await test_db.flush()

    problem = Problem(
        id=uuid.uuid4(),
        title="Two Sum",
        slug="two-sum",
        description="Find two numbers",
        difficulty=Difficulty.EASY,
        pattern=["hash-map"],
        sequence_number=1,
        constraints=["2 <= nums.length <= 10^4"],
        examples={"examples": []},
    )
    test_db.add(problem)
    await test_db.flush()

    link = ImportJobProblem(
        import_job_id=job.id,
        problem_id=problem.id,
    )
    test_db.add(link)
    await test_db.commit()
    await test_db.refresh(job)

    return job, [problem]


@pytest.fixture
async def processing_job(test_db: AsyncSession, test_user_id: str) -> ImportJob:
    """Create an in-progress import job."""
    job = ImportJob(
        id=uuid.uuid4(),
        user_id=test_user_id,
        prompt="Add 5 binary search problems",
        status=ImportJobStatus.PROCESSING,
        message="Generating problem 2 of 5...",
        progress=1,
        total=5,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
    return job


# ── POST /api/imports/ ──


@pytest.mark.asyncio
@patch("app.routes.imports.import_problems_workflow", new_callable=AsyncMock)
async def test_start_import(
    mock_workflow,
    client: AsyncClient,
    auth_headers: dict,
):
    """Test starting an import creates a job and returns it."""
    response = await client.post(
        "/api/imports/",
        json={"prompt": "Add Two Sum from LeetCode"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prompt"] == "Add Two Sum from LeetCode"
    assert data["status"] == "queued"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_start_import_unauthorized(unauthed_client: AsyncClient):
    """Test starting import without auth returns 401."""
    response = await unauthed_client.post(
        "/api/imports/",
        json={"prompt": "Add Two Sum"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_start_import_invalid_prompt(client: AsyncClient, auth_headers: dict):
    """Test import with too-short prompt fails validation."""
    response = await client.post(
        "/api/imports/",
        json={"prompt": "ab"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@patch("app.routes.imports.import_problems_workflow", new_callable=AsyncMock)
async def test_start_import_debounce(
    mock_workflow,
    client: AsyncClient,
    auth_headers: dict,
    test_db: AsyncSession,
    test_user_id: str,
):
    """Test that duplicate prompt with active job returns existing job."""
    # Create an existing queued job with the same prompt
    existing = ImportJob(
        user_id=test_user_id,
        prompt="Add Two Sum from LeetCode",
        status=ImportJobStatus.QUEUED,
        message="Queued",
    )
    test_db.add(existing)
    await test_db.commit()
    await test_db.refresh(existing)

    response = await client.post(
        "/api/imports/",
        json={"prompt": "Add Two Sum from LeetCode"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    # Should return the existing job, not create a new one
    assert data["id"] == str(existing.id)


@pytest.mark.asyncio
async def test_start_import_concurrent_limit(
    client: AsyncClient,
    auth_headers: dict,
    test_db: AsyncSession,
    test_user_id: str,
):
    """Test that exceeding concurrent import limit returns 429."""
    # Create 3 active jobs (the max)
    for i in range(3):
        job = ImportJob(
            user_id=test_user_id,
            prompt=f"Import batch {i}",
            status=ImportJobStatus.PROCESSING,
            message="Processing...",
        )
        test_db.add(job)
    await test_db.commit()

    response = await client.post(
        "/api/imports/",
        json={"prompt": "One more import"},
        headers=auth_headers,
    )

    assert response.status_code == 429
    assert "Maximum" in response.json()["detail"]


# ── GET /api/imports/ ──


@pytest.mark.asyncio
async def test_list_imports(
    client: AsyncClient,
    auth_headers: dict,
    import_job: ImportJob,
):
    """Test listing import jobs returns user's imports."""
    response = await client.get("/api/imports/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(j["id"] == str(import_job.id) for j in data)


@pytest.mark.asyncio
async def test_list_imports_unauthorized(unauthed_client: AsyncClient):
    """Test listing imports without auth returns 401."""
    response = await unauthed_client.get("/api/imports/")
    assert response.status_code == 401


# ── GET /api/imports/{import_id} ──


@pytest.mark.asyncio
async def test_get_import_detail(
    client: AsyncClient,
    auth_headers: dict,
    import_job_with_problems: tuple[ImportJob, list[Problem]],
):
    """Test getting import detail includes linked problems."""
    job, problems = import_job_with_problems

    response = await client.get(f"/api/imports/{job.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(job.id)
    assert data["status"] == "completed"
    assert len(data["problems"]) == 1
    assert data["problems"][0]["title"] == "Two Sum"
    assert data["problems"][0]["slug"] == "two-sum"


@pytest.mark.asyncio
async def test_get_import_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent import returns 404."""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/imports/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_import_invalid_id(client: AsyncClient, auth_headers: dict):
    """Test getting import with invalid UUID returns 400."""
    response = await client.get("/api/imports/not-a-uuid", headers=auth_headers)
    assert response.status_code == 400


# ── POST /api/imports/{import_id}/cancel ──


@pytest.mark.asyncio
async def test_cancel_import(
    client: AsyncClient,
    auth_headers: dict,
    processing_job: ImportJob,
):
    """Test cancelling an in-progress import."""
    response = await client.post(f"/api/imports/{processing_job.id}/cancel", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_completed_import(
    client: AsyncClient,
    auth_headers: dict,
    import_job: ImportJob,
):
    """Test cancelling an already-completed import returns 400."""
    response = await client.post(f"/api/imports/{import_job.id}/cancel", headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_import_not_found(client: AsyncClient, auth_headers: dict):
    """Test cancelling non-existent import returns 404."""
    fake_id = str(uuid.uuid4())
    response = await client.post(f"/api/imports/{fake_id}/cancel", headers=auth_headers)
    assert response.status_code == 404
