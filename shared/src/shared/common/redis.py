from __future__ import annotations

from typing import Any

import redis.asyncio as redis


class RedisClient:
    """Small async Redis wrapper for common operations."""

    def __init__(
        self,
        url: str | None = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        decode_responses: bool = True,
    ) -> None:
        self._client: redis.Redis[str] | redis.Redis[bytes]
        if url:
            if decode_responses:
                self._client = redis.Redis.from_url(url, decode_responses=True)
            else:
                self._client = redis.Redis.from_url(url, decode_responses=False)
        elif decode_responses:
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )
        else:
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,
            )

    async def get(self, key: str) -> Any:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        result = await self._client.set(key, value, ex=expire)
        return bool(result)

    async def delete(self, *keys: str) -> int:
        result = await self._client.delete(*keys)
        return int(result)

    async def publish(self, channel: str, message: str) -> int:
        result = await self._client.publish(channel, message)
        return int(result)

    def pubsub(self) -> redis.client.PubSub:
        return self._client.pubsub()

    async def close(self) -> None:
        await self._client.close()
