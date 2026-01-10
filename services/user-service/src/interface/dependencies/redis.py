"""
Redis dependencies for FastAPI endpoints.
"""

from fastapi import Request

from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.infrastructure.cache.refresh_token_repository import RedisRefreshTokenRepository


async def get_refresh_token_repository(request: Request) -> IRefreshTokenRepository:
    """Provide refresh token repository backed by Redis."""
    if not hasattr(request.app.state, "redis"):
        raise RuntimeError("Redis client not initialized")
    redis_client = request.app.state.redis
    return RedisRefreshTokenRepository(redis_client)
