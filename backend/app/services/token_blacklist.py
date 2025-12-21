"""
Token Blacklist Service using Redis

Provides functionality to blacklist JWT tokens immediately upon logout,
preventing compromised tokens from being used even if they haven't expired.

Security requirement: Tokens must be invalidated immediately to prevent
unauthorized access after logout or token compromise.
"""

from typing import Any, Optional


class TokenBlacklistService:
    """
    Service for managing JWT token blacklist using Redis.

    Uses Redis for fast lookups and automatic TTL-based expiration.
    Keys are stored with format: blacklist:{jti}
    """

    def __init__(self, redis_client: Any) -> None:
        """
        Initialize the TokenBlacklistService.

        Args:
            redis_client: Async Redis client instance
        """
        self.redis: Any = redis_client

    async def blacklist_token(self, jti: str, expires_in_seconds: int) -> None:
        """
        Add a token to the blacklist with automatic expiration.

        Args:
            jti: JWT ID (unique identifier for the token)
            expires_in_seconds: Time until token naturally expires (TTL)

        The token will be automatically removed from Redis after expiration,
        preventing unnecessary storage of old blacklisted tokens.
        """
        if not jti:
            return  # Handle empty JTI gracefully

        key = f"blacklist:{jti}"
        # Store the token with TTL matching its expiration time
        # Value doesn't matter (we only check existence), so use "1"
        await self.redis.setex(key, expires_in_seconds, "1")

    async def is_token_blacklisted(self, jti: Optional[str]) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            jti: JWT ID to check

        Returns:
            True if token is blacklisted, False otherwise

        Performance: O(1) Redis lookup, typically < 1ms
        """
        if not jti:
            return False  # Handle None/empty JTI gracefully

        key = f"blacklist:{jti}"
        exists = await self.redis.exists(key)
        return exists == 1


# Global service instance (will be initialized with Redis client)
_blacklist_service: Optional[TokenBlacklistService] = None


def get_blacklist_service(redis_client: Any) -> TokenBlacklistService:
    """
    Get or create the global TokenBlacklistService instance.

    Args:
        redis_client: Redis client to use for the service

    Returns:
        TokenBlacklistService instance
    """
    global _blacklist_service
    if _blacklist_service is None:
        _blacklist_service = TokenBlacklistService(redis_client)
    return _blacklist_service
