"""Unit tests for notification event consumer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.consumers.event_consumer import NotificationEventConsumer
from src.infrastructure.consumers.processor import NotificationEventProcessor


class _FakeTask:
    def __init__(self) -> None:
        self.cancel = MagicMock()

    def done(self) -> bool:
        return False

    def __await__(self):
        async def _wait() -> None:
            return None

        return _wait().__await__()


def _build_consumer(processor: NotificationEventProcessor) -> NotificationEventConsumer:
    return NotificationEventConsumer(
        bootstrap_servers="kafka:9092",
        group_id="notification-service-group",
        topics=["order-service.order.created"],
        processor=processor,
    )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_event_consumer_start_and_stop_manage_lifecycle() -> None:
    kafka_consumer = AsyncMock()
    kafka_consumer.start = AsyncMock()
    kafka_consumer.stop = AsyncMock()
    fake_task = _FakeTask()
    processor = AsyncMock(spec=NotificationEventProcessor)
    consumer = _build_consumer(processor)

    def _create_task(coro):
        coro.close()
        return fake_task

    with (
        patch("shared.common.kafka.KafkaConsumer", return_value=kafka_consumer),
        patch("asyncio.create_task", side_effect=_create_task),
    ):
        await consumer.start()
        assert consumer.is_ready() is True
        await consumer.stop()

    kafka_consumer.start.assert_awaited_once()
    kafka_consumer.stop.assert_awaited_once()
    fake_task.cancel.assert_called_once()


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_event_consumer_defers_startup_and_retries_in_background() -> None:
    kafka_consumer = AsyncMock()
    kafka_consumer.start = AsyncMock(side_effect=RuntimeError("metadata not ready"))
    kafka_consumer.stop = AsyncMock()
    fake_retry_task = _FakeTask()
    processor = AsyncMock(spec=NotificationEventProcessor)
    consumer = _build_consumer(processor)

    def _create_task(coro):
        coro.close()
        return fake_retry_task

    with (
        patch("shared.common.kafka.KafkaConsumer", return_value=kafka_consumer),
        patch("asyncio.create_task", side_effect=_create_task),
    ):
        await consumer.start()
        assert consumer.is_ready() is False
        await consumer.stop()

    kafka_consumer.start.assert_awaited_once()
    kafka_consumer.stop.assert_awaited_once()
    fake_retry_task.cancel.assert_called_once()
