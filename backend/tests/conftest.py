"""Pytest configuration and fixtures."""

import asyncio
import os
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from supabase import acreate_client, create_client

from app.config.settings import settings
from app.db.connection import get_db
from app.db.tables import (
    Base,
    Difficulty,
    Language,
    Problem,
    ProblemLanguage,
    Submission,
    TestCase,
    UserProgress,
)
from app.main import app


# Use separate test database (port 54325) to avoid destroying dev/prod data
# Set TEST_DATABASE_URL env var to override, or use default test container
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:54325/acodeaday_test",
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def setup_database():
    """Run migrations once before all tests."""
    import subprocess

    # Run alembic with DATABASE_URL env var set to test database
    # This ensures env.py (which reads from settings) uses the test URL
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL

    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=str(Path(__file__).parent.parent),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")
    yield


@pytest.fixture(scope="function")
async def test_engine(setup_database):
    """Create test database engine - function scoped for proper async handling."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )
    yield engine

    # Cleanup: truncate all tables after each test (preserves schema)
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Initialize async app.state.supabase for tests (normally done in lifespan)
    app.state.supabase = await acreate_client(settings.supabase_url, settings.supabase_key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_user_session() -> dict:
    """
    Login with Supabase Auth and return session info.

    Uses default_user_email and default_user_password from settings to authenticate
    with Supabase and retrieve a valid JWT token and user ID.
    """
    # Create Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    # Login with email/password
    email = settings.default_user_email
    password = settings.default_user_password

    try:
        # Try to sign in first
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception:
        # If sign in fails, create the user first then sign in
        supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

    return {
        "access_token": response.session.access_token,
        "user_id": response.user.id,
    }


@pytest.fixture(scope="session")
def auth_headers(test_user_session: dict) -> dict:
    """Return Bearer token headers for authenticated requests."""
    return {"Authorization": f"Bearer {test_user_session['access_token']}"}


@pytest.fixture(scope="session")
def test_user_id(test_user_session: dict) -> str:
    """Return the test user's Supabase user ID."""
    return test_user_session["user_id"]


# =============================================================================
# Problem Fixtures
# =============================================================================


@pytest.fixture
async def sample_problem(test_db: AsyncSession) -> Problem:
    """Create a sample problem with language config and test cases."""
    problem = Problem(
        id=uuid.uuid4(),
        title="Two Sum",
        slug="two-sum",
        description="Find two numbers that add up to target",
        difficulty=Difficulty.EASY,
        pattern="hash-map",
        sequence_number=1,
        constraints=["2 <= nums.length <= 10^4"],
        examples={
            "examples": [
                {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"}
            ]
        },
    )
    test_db.add(problem)
    await test_db.flush()

    # Add language config
    problem_lang = ProblemLanguage(
        problem_id=problem.id,
        language=Language.PYTHON,
        starter_code="class Solution:\n    def twoSum(self, nums, target):\n        pass",
        reference_solution="class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
        function_signature={"name": "twoSum", "params": ["nums", "target"]},
    )
    test_db.add(problem_lang)

    # Add test cases
    test_cases = [
        TestCase(
            problem_id=problem.id,
            input=[[2, 7, 11, 15], 9],
            expected=[0, 1],
            is_hidden=False,
            sequence=1,
        ),
        TestCase(
            problem_id=problem.id,
            input=[[3, 2, 4], 6],
            expected=[1, 2],
            is_hidden=True,
            sequence=2,
        ),
    ]
    test_db.add_all(test_cases)
    await test_db.commit()
    await test_db.refresh(problem)

    return problem


# =============================================================================
# Progress Fixtures
# =============================================================================


@pytest.fixture
async def problems_with_progress(
    test_db: AsyncSession, test_user_id: str
) -> list[Problem]:
    """Create problems with user progress for testing."""
    problems = []

    # Problem 1: Due for review
    p1 = Problem(
        id=uuid.uuid4(),
        title="Problem 1",
        slug="problem-1",
        description="Test problem 1",
        difficulty=Difficulty.EASY,
        pattern="array",
        sequence_number=1,
        constraints=["constraint 1"],
        examples={"examples": []},
    )
    test_db.add(p1)
    await test_db.flush()
    problems.append(p1)

    # User progress: due for review
    progress1 = UserProgress(
        user_id=test_user_id,
        problem_id=p1.id,
        times_solved=1,
        last_solved_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=10),
        next_review_date=date.today() - timedelta(days=1),  # Overdue
        is_mastered=False,
    )
    test_db.add(progress1)

    # Problem 2: Already mastered
    p2 = Problem(
        id=uuid.uuid4(),
        title="Problem 2",
        slug="problem-2",
        description="Test problem 2",
        difficulty=Difficulty.MEDIUM,
        pattern="hash-map",
        sequence_number=2,
        constraints=["constraint 2"],
        examples={"examples": []},
    )
    test_db.add(p2)
    await test_db.flush()
    problems.append(p2)

    progress2 = UserProgress(
        user_id=test_user_id,
        problem_id=p2.id,
        times_solved=2,
        last_solved_at=datetime.now(UTC).replace(tzinfo=None),
        next_review_date=None,
        is_mastered=True,
    )
    test_db.add(progress2)

    # Problem 3: New (no progress)
    p3 = Problem(
        id=uuid.uuid4(),
        title="Problem 3",
        slug="problem-3",
        description="Test problem 3",
        difficulty=Difficulty.HARD,
        pattern="tree",
        sequence_number=3,
        constraints=["constraint 3"],
        examples={"examples": []},
    )
    test_db.add(p3)
    problems.append(p3)

    await test_db.commit()
    return problems


# =============================================================================
# Submission Fixtures
# =============================================================================


@pytest.fixture
async def problem_with_submissions(
    test_db: AsyncSession, test_user_id: str
) -> tuple[Problem, list[Submission]]:
    """Create a problem with submission history."""
    problem = Problem(
        id=uuid.uuid4(),
        title="Two Sum",
        slug="two-sum",
        description="Test problem",
        difficulty=Difficulty.EASY,
        pattern="array",
        sequence_number=1,
        constraints=["constraint"],
        examples={"examples": []},
    )
    test_db.add(problem)
    await test_db.flush()

    # Create submissions
    submissions = [
        Submission(
            user_id=test_user_id,
            problem_id=problem.id,
            code="class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]",
            language=Language.PYTHON,
            passed=True,
            runtime_ms=15,
        ),
        Submission(
            user_id=test_user_id,
            problem_id=problem.id,
            code="class Solution:\n    def twoSum(self, nums, target):\n        return []",
            language=Language.PYTHON,
            passed=False,
            runtime_ms=10,
        ),
    ]
    test_db.add_all(submissions)
    await test_db.commit()

    return problem, submissions
