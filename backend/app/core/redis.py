"""
Redis connection management for caching and token blacklisting
"""

from typing import Any, AsyncGenerator

from redis.asyncio import Redis

from app.core.config import settings

# Global Redis client instance
_redis_client: Any = None


async def get_redis() -> AsyncGenerator[Any, None]:
    """
    Dependency to get Redis client.

    Yields:
        Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=False)

    yield _redis_client


async def close_redis() -> None:
    """Close the Redis connection on shutdown"""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
