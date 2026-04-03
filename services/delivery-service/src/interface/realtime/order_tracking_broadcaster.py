"""Order tracking broadcaster with Redis Pub/Sub and in-memory fallback."""

import asyncio
from collections import defaultdict
from contextlib import suppress
import json
from typing import Any
from uuid import UUID

from fastapi import WebSocket
import redis.asyncio as redis


class OrderTrackingBroadcaster:
    """Track websocket subscribers and distribute updates per order id."""

    def __init__(
        self,
        realtime_backend: str,
        redis_host: str,
        redis_port: int,
        redis_db: int,
        redis_password: str | None,
        redis_channel_prefix: str,
    ) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._listener_tasks: dict[UUID, asyncio.Task[None]] = {}
        self._redis_client: redis.Redis | None = None
        self._redis_enabled = realtime_backend.lower() == "redis"
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_db = redis_db
        self._redis_password = redis_password
        self._redis_channel_prefix = redis_channel_prefix

    async def connect(self, order_id: UUID, websocket: WebSocket) -> None:
        """Accept websocket connection for order stream."""
        await websocket.accept()
        self._connections[order_id].add(websocket)

        if self._redis_enabled and order_id not in self._listener_tasks:
            self._listener_tasks[order_id] = asyncio.create_task(self._consume_channel(order_id))

    def disconnect(self, order_id: UUID, websocket: WebSocket) -> None:
        """Remove websocket connection from order stream."""
        connections = self._connections.get(order_id)
        if not connections:
            return

        connections.discard(websocket)
        if not connections:
            self._connections.pop(order_id, None)

    async def broadcast(self, order_id: UUID, event: dict[str, Any]) -> None:
        """Broadcast event payload to all subscribers for order."""
        if self._redis_enabled and await self._publish_to_redis(order_id, event):
            return

        await self._broadcast_local(order_id, event)

    async def close(self) -> None:
        """Shutdown broadcaster resources."""
        for task in self._listener_tasks.values():
            task.cancel()
        if self._listener_tasks:
            await asyncio.gather(*self._listener_tasks.values(), return_exceptions=True)
        self._listener_tasks.clear()

        if self._redis_client is not None:
            await self._redis_client.aclose()
            self._redis_client = None

    def _channel(self, order_id: UUID) -> str:
        return f"{self._redis_channel_prefix}:{order_id}"

    def _get_redis_client(self) -> redis.Redis:
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self._redis_host,
                port=self._redis_port,
                db=self._redis_db,
                password=self._redis_password,
                decode_responses=True,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
        return self._redis_client

    async def _publish_to_redis(self, order_id: UUID, event: dict[str, Any]) -> bool:
        published = False
        try:
            client = self._get_redis_client()
            await client.publish(self._channel(order_id), json.dumps(event))
            published = True
        except Exception:
            published = False
        return published

    async def _broadcast_local(self, order_id: UUID, event: dict[str, Any]) -> None:
        connections = list(self._connections.get(order_id, set()))
        for connection in connections:
            try:
                await connection.send_json(event)
            except Exception:
                self.disconnect(order_id, connection)

    async def _consume_channel(self, order_id: UUID) -> None:
        client = self._get_redis_client()
        pubsub = client.pubsub()
        channel = self._channel(order_id)

        try:
            await pubsub.subscribe(channel)
            while True:
                if not self._connections.get(order_id):
                    break

                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    await asyncio.sleep(0.05)
                    continue

                event = self._deserialize_event(message.get("data"))
                if event is None:
                    continue

                await self._broadcast_local(order_id, event)
        except asyncio.CancelledError:
            raise
        except Exception:
            return
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(channel)
            with suppress(Exception):
                await pubsub.aclose()
            self._listener_tasks.pop(order_id, None)

    @staticmethod
    def _deserialize_event(payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8")
            except Exception:
                return None
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except Exception:
                return None
            if isinstance(parsed, dict):
                return parsed
        return None
