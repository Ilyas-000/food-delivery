from __future__ import annotations

from collections.abc import AsyncIterator, Callable
import json
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import ConsumerRecord
from pydantic import BaseModel

Serializer = Callable[[Any], bytes]


def _default_serializer(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return value.model_dump_json().encode("utf-8")
    if isinstance(value, dict | list):
        return json.dumps(value).encode("utf-8")
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


class KafkaProducer:
    """Kafka producer wrapper."""

    def __init__(
        self,
        bootstrap_servers: str,
        serializer: Serializer | None = None,
        **kwargs: Any,
    ) -> None:
        self._serializer = serializer or _default_serializer
        self._producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers, **kwargs)

    async def start(self) -> None:
        await self._producer.start()

    async def stop(self) -> None:
        await self._producer.stop()

    async def send(
        self,
        topic: str,
        value: Any,
        key: str | bytes | None = None,
    ) -> None:
        payload = self._serializer(value)
        key_bytes = key.encode("utf-8") if isinstance(key, str) else key
        await self._producer.send_and_wait(topic, payload, key=key_bytes)


class KafkaConsumer:
    """Kafka consumer wrapper."""

    def __init__(
        self,
        topics: list[str],
        bootstrap_servers: str,
        group_id: str,
        **kwargs: Any,
    ) -> None:
        self._consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            **kwargs,
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def consume(self) -> AsyncIterator[ConsumerRecord]:
        async for message in self._consumer:
            yield message
