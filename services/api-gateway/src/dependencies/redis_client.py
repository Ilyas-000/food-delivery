"""Redis dependency helpers for API Gateway."""

import asyncio

from shared.common.redis import RedisClient

from src.config import settings

_redis_client: RedisClient | None = None


async def init_redis() -> None:
    """Initialize Redis client if rate limiting is enabled."""
    global _redis_client
    if not settings.rate_limit_enabled:
        return

    _redis_client = RedisClient(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=True,
    )
    last_error: Exception | None = None
    for attempt in range(1, settings.redis_connect_retries + 1):
        try:
            await _redis_client.ping()
            return
        except Exception as exc:  # pragma: no cover - network timing issues
            last_error = exc
            if attempt == settings.redis_connect_retries:
                break
            await asyncio.sleep(settings.redis_connect_delay_seconds)
    raise RuntimeError("Redis is unavailable after retries") from last_error


async def close_redis() -> None:
    """Close Redis client on shutdown."""
    if _redis_client is not None:
        await _redis_client.close()


def get_redis() -> RedisClient:
    """Get Redis client for rate limiting."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client
