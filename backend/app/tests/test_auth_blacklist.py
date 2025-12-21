"""
Tests for JWT token blacklisting integration with authentication

Security requirement: Tokens must be blacklisted on logout and rejected when blacklisted.

Following TDD: These tests should FAIL initially, then PASS after implementation.
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, hash_password
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_logout_blacklists_access_token(client: TestClient, db_session: AsyncSession) -> None:
    """
    Test that logout blacklists the access token.

    Expected behavior:
    - User logs in and gets access token
    - User can access protected endpoints with token
    - User logs out
    - Access token is blacklisted
    - Same token cannot be used anymore (401 Unauthorized)
    """
    # Create a test user
    user = User(
        email="blacklisttest@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "blacklisttest@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Verify token works before logout
    me_response_before = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response_before.status_code == 200

    # Logout (should blacklist access token)
    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200

    # Try to use the same access token (should fail - token is blacklisted)
    me_response_after = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response_after.status_code == 401
    assert "blacklisted" in me_response_after.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_blacklists_refresh_token(
    client: TestClient, db_session: AsyncSession
) -> None:
    """
    Test that logout blacklists the refresh token.

    Expected behavior:
    - User logs in and gets tokens
    - User logs out
    - Refresh token is blacklisted
    - Cannot use refresh token to get new access token
    """
    # Create a test user
    user = User(
        email="refreshblacklist@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "refreshblacklist@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Try to use blacklisted refresh token
    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401
    assert "blacklisted" in refresh_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_token_blacklist_persists_in_redis(
    client: TestClient, db_session: AsyncSession
) -> None:
    """
    Test that token blacklist is stored in Redis correctly.

    Expected behavior:
    - After logout, token JTI is in Redis
    - Redis key follows format: blacklist:{jti}
    - TTL is set to token expiration time
    """
    # Create a test user
    user = User(
        email="redistest@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "redistest@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Decode token to get JTI
    payload = decode_token(access_token)
    assert payload is not None
    jti = payload.get("jti")
    assert jti is not None, "Token should have JTI claim"

    # Logout
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Check Redis directly
    redis_client: Any = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)
    try:
        key = f"blacklist:{jti}"
        exists = await redis_client.exists(key)
        assert exists == 1, f"Blacklisted token {jti} should exist in Redis"

        # Check TTL is set
        ttl = await redis_client.ttl(key)
        assert ttl > 0, "TTL should be set on blacklisted token"
    finally:
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_new_login_after_logout_works(client: TestClient, db_session: AsyncSession) -> None:
    """
    Test that user can login again after logout.

    Expected behavior:
    - User logs in, gets tokens
    - User logs out (tokens blacklisted)
    - User logs in again (gets NEW tokens)
    - New tokens work fine
    """
    # Create a test user
    user = User(
        email="relogintest@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # First login
    login1 = client.post(
        "/api/v1/auth/login",
        json={"email": "relogintest@example.com", "password": "password123"},
    )
    access1 = login1.json()["access_token"]
    refresh1 = login1.json()["refresh_token"]

    # Logout
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh1},
        headers={"Authorization": f"Bearer {access1}"},
    )

    # Second login (should work)
    login2 = client.post(
        "/api/v1/auth/login",
        json={"email": "relogintest@example.com", "password": "password123"},
    )
    assert login2.status_code == 200
    access2 = login2.json()["access_token"]

    # New token should work
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access2}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "relogintest@example.com"


@pytest.mark.asyncio
async def test_tokens_have_unique_jti(client: TestClient, db_session: AsyncSession) -> None:
    """
    Test that each token has a unique JWT ID (jti).

    Expected behavior:
    - Every token generated has a unique jti
    - Access and refresh tokens have different jtis
    - Multiple logins create different jtis
    """
    # Create a test user
    user = User(
        email="jtitest@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.SUBMITTER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login twice
    login1 = client.post(
        "/api/v1/auth/login",
        json={"email": "jtitest@example.com", "password": "password123"},
    )
    login2 = client.post(
        "/api/v1/auth/login",
        json={"email": "jtitest@example.com", "password": "password123"},
    )

    # Decode all tokens
    access1 = decode_token(login1.json()["access_token"])
    refresh1 = decode_token(login1.json()["refresh_token"])
    access2 = decode_token(login2.json()["access_token"])
    refresh2 = decode_token(login2.json()["refresh_token"])

    # All should have jtis
    assert access1 and access1.get("jti")
    assert refresh1 and refresh1.get("jti")
    assert access2 and access2.get("jti")
    assert refresh2 and refresh2.get("jti")

    # All jtis should be unique
    jtis = {
        access1["jti"],
        refresh1["jti"],
        access2["jti"],
        refresh2["jti"],
    }
    assert len(jtis) == 4, "All tokens should have unique jtis"
