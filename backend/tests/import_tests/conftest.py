"""Test fixtures for import feature tests.

Uses a local PostgreSQL database directly (no Supabase Auth dependency).
Auth middleware is mocked to return a fake user.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import connection as connection_module
from app.db.connection import get_db
from app.db.tables import Base
from app.main import app
from app.middleware.auth import get_current_user
from app.services import import_workflow as workflow_module

# Use local PostgreSQL (no Docker/Supabase required)
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/acodeaday_test",
)

FAKE_USER_ID = "test-user-00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True, echo=False)
    yield engine

    # Truncate all tables after each test
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
def test_user_id() -> str:
    return FAKE_USER_ID


@pytest.fixture(scope="function")
def auth_headers() -> dict:
    return {"Authorization": "Bearer fake-test-token"}


@pytest.fixture(scope="function", autouse=True)
async def patch_async_session_local(test_engine):
    """Redirect AsyncSessionLocal to use the test engine.

    This ensures workflow helpers (_update_job, _is_cancelled, _persist_problem,
    recover_stuck_import_jobs) all use the test database.

    We must patch both the connection module AND the workflow module because
    `from app.db.connection import AsyncSessionLocal` creates a local binding.
    """
    test_session_local = async_sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    orig_connection = connection_module.AsyncSessionLocal
    orig_workflow = workflow_module.AsyncSessionLocal
    connection_module.AsyncSessionLocal = test_session_local
    workflow_module.AsyncSessionLocal = test_session_local
    yield
    connection_module.AsyncSessionLocal = orig_connection
    workflow_module.AsyncSessionLocal = orig_workflow


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client with mocked auth and DB."""

    async def override_get_db():
        yield test_db

    async def override_get_current_user():
        return {"id": FAKE_USER_ID, "email": "test@example.com"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def unauthed_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client WITHOUT auth override — for testing 401 responses."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    # Do NOT override get_current_user — let it use real auth (which will fail)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
