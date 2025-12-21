"""
Pytest configuration and shared fixtures for backend tests
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Configure test CORS origins BEFORE importing app
os.environ["CORS_ORIGINS"] = (
    "http://localhost:3000,"
    "https://app.example.com,"
    "https://staging.ans.postxsociety.cloud,"
    "https://ans.postxsociety.cloud"
)

from redis.asyncio import Redis  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

# Reload settings to pick up test environment variables
settings.CORS_ORIGINS = os.environ["CORS_ORIGINS"]


# Override Redis dependency for tests to create new client per test
@pytest_asyncio.fixture
async def test_redis_client() -> AsyncGenerator[Any, None]:
    """Provide a fresh Redis client for each test"""
    client: Any = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)
    try:
        yield client
    finally:
        # Clean up: flush test data and close properly
        try:
            await client.flushdb()
        except Exception:
            pass  # Ignore errors during cleanup
        try:
            await client.aclose()
        except Exception:
            pass  # Ignore errors during close


@pytest.fixture(scope="session")
def event_loop() -> Generator[Any, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a test database session.
    Uses in-memory SQLite for fast tests.
    """
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession, test_redis_client: Any) -> Generator[TestClient, None, None]:
    """
    Provide a test client with database and Redis session overrides.
    """

    def override_get_db() -> AsyncSession:
        """Override get_db dependency to use test database"""
        return db_session

    async def override_get_redis() -> AsyncGenerator[Any, None]:
        """Override get_redis dependency to use test Redis client"""
        yield test_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_user(db_session: AsyncSession) -> tuple[User, str]:
    """
    Create an authenticated test user and return the user and their JWT token.

    Returns:
        Tuple of (User object, JWT token string)
    """
    user = User(
        email="testuser@example.com",
        password_hash="hashed_password",
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Generate JWT token for this user
    token = create_access_token(data={"sub": str(user.id)})

    return user, token
