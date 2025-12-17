"""
Pytest configuration and shared fixtures for backend tests
"""

import asyncio
from typing import AsyncGenerator, Generator, Tuple

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole


@pytest.fixture(scope="session")
def event_loop() -> Generator:
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
def client(db_session: AsyncSession) -> TestClient:
    """
    Provide a test client with database session override.
    """

    def override_get_db() -> AsyncSession:
        """Override get_db dependency to use test database"""
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_user(db_session: AsyncSession) -> Tuple[User, str]:
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
