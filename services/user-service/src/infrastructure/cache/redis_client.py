"""
Redis client factory for user service.
"""

from shared.common.redis import RedisClient
from src.config import settings


def create_redis_client() -> RedisClient:
    """Create a new Redis client instance."""
    return RedisClient(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=True,
    )


async def close_redis_client(client: RedisClient) -> None:
    """Close provided Redis client."""
    await client.close()
