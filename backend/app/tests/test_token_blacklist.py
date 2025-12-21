"""
Tests for JWT Token Blacklist Service using Redis

Security requirement: Tokens must be invalidated immediately upon logout
to prevent unauthorized access with compromised tokens.

Following TDD: These tests should FAIL initially, then PASS after implementation.
"""

import asyncio
import time
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from app.core.config import settings
from app.services.token_blacklist import TokenBlacklistService


@pytest_asyncio.fixture
async def redis_client() -> Any:
    """Provide a Redis client for testing"""
    client: Any = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)
    yield client
    # Clean up: flush test data
    await client.flushdb()
    await client.close()


@pytest_asyncio.fixture
async def blacklist_service(redis_client: Any) -> TokenBlacklistService:
    """Provide a TokenBlacklistService instance for testing"""
    return TokenBlacklistService(redis_client)


@pytest.mark.asyncio
async def test_blacklist_token(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that a token can be blacklisted with TTL.

    Expected behavior:
    - Token JTI is added to Redis
    - TTL is set to token expiration time
    - Blacklisted token is detected as blacklisted
    """
    jti = str(uuid4())
    expires_in_seconds = 900  # 15 minutes

    # Act: Blacklist the token
    await blacklist_service.blacklist_token(jti, expires_in_seconds)

    # Assert: Token should be blacklisted
    is_blacklisted = await blacklist_service.is_token_blacklisted(jti)
    assert is_blacklisted is True, f"Token {jti} should be blacklisted"


@pytest.mark.asyncio
async def test_non_blacklisted_token(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that a non-blacklisted token is not detected as blacklisted.

    Expected behavior:
    - Token JTI not in Redis returns False
    """
    jti = str(uuid4())

    # Act: Check non-blacklisted token
    is_blacklisted = await blacklist_service.is_token_blacklisted(jti)

    # Assert: Token should NOT be blacklisted
    assert is_blacklisted is False, f"Token {jti} should not be blacklisted"


@pytest.mark.asyncio
async def test_blacklist_token_with_ttl(
    blacklist_service: TokenBlacklistService, redis_client: Any
) -> None:
    """
    Test that blacklisted tokens have correct TTL set in Redis.

    Expected behavior:
    - TTL is set on the Redis key
    - TTL matches the expiration time
    """
    jti = str(uuid4())
    expires_in_seconds = 900  # 15 minutes

    # Act: Blacklist the token
    await blacklist_service.blacklist_token(jti, expires_in_seconds)

    # Assert: Check TTL in Redis
    key = f"blacklist:{jti}"
    ttl = await redis_client.ttl(key)

    # TTL should be close to expires_in_seconds (allow 5 second variance)
    assert ttl > 0, "TTL should be set"
    assert (
        expires_in_seconds - 5 <= ttl <= expires_in_seconds
    ), f"TTL {ttl} should be close to {expires_in_seconds}"


@pytest.mark.asyncio
async def test_blacklist_token_auto_expires(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that blacklisted tokens automatically expire from Redis.

    Expected behavior:
    - After TTL expires, token is no longer blacklisted
    - Redis automatically removes expired keys
    """
    jti = str(uuid4())
    expires_in_seconds = 2  # 2 seconds for fast test

    # Act: Blacklist the token with short TTL
    await blacklist_service.blacklist_token(jti, expires_in_seconds)

    # Assert: Token is initially blacklisted
    assert await blacklist_service.is_token_blacklisted(jti) is True

    # Wait for token to expire
    await asyncio.sleep(3)

    # Assert: Token should no longer be blacklisted
    is_blacklisted = await blacklist_service.is_token_blacklisted(jti)
    assert is_blacklisted is False, "Token should have auto-expired from blacklist"


@pytest.mark.asyncio
async def test_blacklist_multiple_tokens(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that multiple tokens can be blacklisted independently.

    Expected behavior:
    - Each token has its own blacklist entry
    - Checking one token doesn't affect others
    """
    jti1 = str(uuid4())
    jti2 = str(uuid4())
    jti3 = str(uuid4())

    # Act: Blacklist two tokens
    await blacklist_service.blacklist_token(jti1, 900)
    await blacklist_service.blacklist_token(jti2, 900)

    # Assert: Check each token independently
    assert await blacklist_service.is_token_blacklisted(jti1) is True
    assert await blacklist_service.is_token_blacklisted(jti2) is True
    assert (
        await blacklist_service.is_token_blacklisted(jti3) is False
    ), "Non-blacklisted token should not be affected"


@pytest.mark.asyncio
async def test_blacklist_performance(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that blacklist operations meet performance requirements.

    Requirement: < 10ms per request
    Expected behavior:
    - Blacklist check should complete in under 10ms
    - Blacklist operation should complete in under 10ms
    """
    jti = str(uuid4())

    # Measure blacklist operation
    start_time = time.perf_counter()
    await blacklist_service.blacklist_token(jti, 900)
    blacklist_duration = (time.perf_counter() - start_time) * 1000  # Convert to ms

    # Measure check operation
    start_time = time.perf_counter()
    await blacklist_service.is_token_blacklisted(jti)
    check_duration = (time.perf_counter() - start_time) * 1000  # Convert to ms

    # Assert: Operations should be fast
    assert blacklist_duration < 10, f"Blacklist operation took {blacklist_duration:.2f}ms (> 10ms)"
    assert check_duration < 10, f"Blacklist check took {check_duration:.2f}ms (> 10ms)"


@pytest.mark.asyncio
async def test_blacklist_redis_key_format(
    blacklist_service: TokenBlacklistService, redis_client: Any
) -> None:
    """
    Test that Redis keys follow expected format for monitoring/debugging.

    Expected format: blacklist:{jti}
    """
    jti = str(uuid4())

    # Act: Blacklist the token
    await blacklist_service.blacklist_token(jti, 900)

    # Assert: Check key exists with correct format
    expected_key = f"blacklist:{jti}"
    exists = await redis_client.exists(expected_key)
    assert exists == 1, f"Key {expected_key} should exist in Redis"


@pytest.mark.asyncio
async def test_blacklist_handles_invalid_jti(
    blacklist_service: TokenBlacklistService,
) -> None:
    """
    Test that blacklist service handles invalid/empty JTI gracefully.

    Expected behavior:
    - Should not crash on empty string
    - Should handle None gracefully
    """
    # Act & Assert: Should not raise exceptions
    try:
        await blacklist_service.is_token_blacklisted("")
        # Test with None - expect graceful handling (mypy will warn, but we want to test this)
        result = await blacklist_service.is_token_blacklisted(None)  # type: ignore
        assert result is False
    except Exception as e:
        pytest.fail(f"Blacklist service should handle invalid JTI gracefully: {e}")
