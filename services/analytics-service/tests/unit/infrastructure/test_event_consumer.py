"""Unit tests for analytics event consumer."""

from collections.abc import AsyncIterator
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.consumers.event_consumer import AnalyticsEventConsumer
from src.infrastructure.consumers.processor import AnalyticsEventProcessor


class _FakeTask:
    def __init__(self) -> None:
        self.cancel = MagicMock()

    def done(self) -> bool:
        return False

    def __await__(self):
        async def _wait() -> None:
            return None

        return _wait().__await__()


def _build_consumer(processor: AnalyticsEventProcessor) -> AnalyticsEventConsumer:
    return AnalyticsEventConsumer(
        bootstrap_servers="kafka:9092",
        group_id="analytics-service-group",
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
    processor = AsyncMock(spec=AnalyticsEventProcessor)
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


async def _message_stream() -> AsyncIterator[SimpleNamespace]:
    yield SimpleNamespace(value=json.dumps({"event_type": "custom.event"}).encode("utf-8"))


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_event_consumer_consume_loop_processes_messages() -> None:
    processor = AsyncMock(spec=AnalyticsEventProcessor)
    consumer = _build_consumer(processor)
    consumer._consumer = SimpleNamespace(consume=_message_stream)

    await consumer._consume_loop()

    processor.process_event.assert_awaited_once_with({"event_type": "custom.event"})
