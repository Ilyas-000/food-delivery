"""Kafka consumer manager for notification events."""

import asyncio
from contextlib import suppress
import json
from typing import Any

import structlog

from src.infrastructure.consumers.processor import NotificationEventProcessor

logger = structlog.get_logger(__name__)


class NotificationEventConsumer:
    """Manage Kafka consumer lifecycle for notification events."""

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        processor: NotificationEventProcessor,
        auto_offset_reset: str = "earliest",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._processor = processor
        self._auto_offset_reset = auto_offset_reset
        self._consumer: Any | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start Kafka consumer loop."""
        if self._consumer is not None:
            return

        try:
            from shared.common.kafka import KafkaConsumer
        except ModuleNotFoundError:
            logger.warning("notification.consumer.shared_module_missing")
            return

        consumer = KafkaConsumer(
            topics=self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset=self._auto_offset_reset,
        )
        await consumer.start()
        self._consumer = consumer
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "notification.consumer.started",
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            topics=self._topics,
        )

    async def stop(self) -> None:
        """Stop Kafka consumer loop."""
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
            logger.info("notification.consumer.stopped")

    def is_ready(self) -> bool:
        """Return current consumer readiness state."""
        return self._consumer is not None and self._task is not None and not self._task.done()

    async def _consume_loop(self) -> None:
        """Consume Kafka messages and pass them to processor."""
        consumer = self._consumer
        if consumer is None:
            msg = "Kafka consumer loop started without an initialized consumer"
            raise RuntimeError(msg)

        async for message in consumer.consume():
            try:
                payload = json.loads(message.value.decode("utf-8"))
                await self._processor.process_event(payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("notification.consumer.message_failed")
