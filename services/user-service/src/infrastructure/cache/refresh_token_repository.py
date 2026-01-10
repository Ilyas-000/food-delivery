"""
Redis implementation of refresh token storage (whitelist by JTI).
"""

from uuid import UUID

from shared.common.redis import RedisClient
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository

_REFRESH_TOKEN_PREFIX = "refresh_token:jti:"  # nosec B105 - Redis key prefix, not a secret


class RedisRefreshTokenRepository(IRefreshTokenRepository):
    """Store active refresh token JTIs in Redis."""

    def __init__(self, client: RedisClient) -> None:
        self._client = client

    async def store(self, jti: str, user_id: UUID, expires_in: int) -> None:
        key = f"{_REFRESH_TOKEN_PREFIX}{jti}"
        await self._client.set(key, str(user_id), expire=expires_in)

    async def exists(self, jti: str) -> bool:
        key = f"{_REFRESH_TOKEN_PREFIX}{jti}"
        value = await self._client.get(key)
        return value is not None

    async def delete(self, jti: str) -> None:
        key = f"{_REFRESH_TOKEN_PREFIX}{jti}"
        await self._client.delete(key)
