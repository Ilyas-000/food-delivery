"""Kafka consumer manager for analytics events."""

import asyncio
from contextlib import suppress
import json
from typing import Any

import structlog

from src.infrastructure.consumers.processor import AnalyticsEventProcessor

logger = structlog.get_logger(__name__)


class AnalyticsEventConsumer:
    """Manage Kafka consumer lifecycle for analytics ingestion."""

    _startup_retry_seconds = 2.0

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        group_id: str,
        topics: list[str],
        processor: AnalyticsEventProcessor,
        auto_offset_reset: str = "earliest",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._processor = processor
        self._auto_offset_reset = auto_offset_reset
        self._consumer: Any | None = None
        self._task: asyncio.Task[None] | None = None
        self._retry_task: asyncio.Task[None] | None = None
        self._stopping = False

    async def start(self) -> None:
        """Start Kafka consumer loop."""
        if self._consumer is not None or (
            self._retry_task is not None and not self._retry_task.done()
        ):
            return

        self._stopping = False
        try:
            await self._start_consumer_once()
        except Exception:
            logger.warning(
                "analytics.consumer.start_deferred",
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                topics=self._topics,
            )
            self._retry_task = asyncio.create_task(self._retry_until_started())

    async def _start_consumer_once(self) -> None:
        """Start Kafka consumer once, raising if Kafka metadata is not ready yet."""
        try:
            from shared.common.kafka import KafkaConsumer
        except ModuleNotFoundError:
            logger.warning("analytics.consumer.shared_module_missing")
            return

        consumer = KafkaConsumer(
            topics=self._topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset=self._auto_offset_reset,
        )
        try:
            await consumer.start()
        except Exception:
            with suppress(Exception):
                await consumer.stop()
            raise

        self._consumer = consumer
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(
            "analytics.consumer.started",
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            topics=self._topics,
        )

    async def stop(self) -> None:
        """Stop Kafka consumer loop."""
        self._stopping = True

        if self._retry_task is not None:
            self._retry_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._retry_task
            self._retry_task = None

        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
            logger.info("analytics.consumer.stopped")

    def is_ready(self) -> bool:
        """Return current consumer readiness state."""
        return self._consumer is not None and self._task is not None and not self._task.done()

    async def _retry_until_started(self) -> None:
        """Retry consumer startup without blocking the HTTP application boot."""
        while not self._stopping and self._consumer is None:
            try:
                await self._start_consumer_once()
                self._retry_task = None
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning(
                    "analytics.consumer.start_retrying",
                    retry_in_seconds=self._startup_retry_seconds,
                )
                await asyncio.sleep(self._startup_retry_seconds)
            else:
                return

    async def _consume_loop(self) -> None:
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
                logger.exception("analytics.consumer.message_failed")
