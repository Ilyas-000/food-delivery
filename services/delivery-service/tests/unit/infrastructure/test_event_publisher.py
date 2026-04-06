"""Unit tests for delivery Kafka publisher resilience."""

import asyncio
from collections.abc import Generator
from typing import ClassVar

import pytest

from shared.events.delivery_events import DeliveryAssignedEvent
from src.infrastructure.events import publisher

EXPECTED_RECONNECT_STARTS = 2
EXPECTED_STOPS = 1


class FakeKafkaProducer:
    """Controllable Kafka producer test double."""

    start_failures: ClassVar[int] = 0
    send_failures: ClassVar[int] = 0
    starts: ClassVar[int] = 0
    stops: ClassVar[int] = 0
    sent_messages: ClassVar[list[tuple[str, str]]] = []

    def __init__(self, **_: object) -> None:
        self.started = False

    @classmethod
    def reset(cls) -> None:
        cls.start_failures = 0
        cls.send_failures = 0
        cls.starts = 0
        cls.stops = 0
        cls.sent_messages = []

    async def start(self) -> None:
        type(self).starts += 1
        if type(self).start_failures > 0:
            type(self).start_failures -= 1
            raise RuntimeError("kafka unavailable")
        self.started = True

    async def stop(self) -> None:
        type(self).stops += 1
        self.started = False

    async def send(self, topic: str, value: object, key: str | None = None) -> None:
        _ = value
        if type(self).send_failures > 0:
            type(self).send_failures -= 1
            raise RuntimeError("broken pipe")
        type(self).sent_messages.append((topic, key or ""))


@pytest.fixture(autouse=True)
def _reset_publisher_state(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Reset singleton publisher state between tests."""
    import shared.common.kafka as shared_kafka

    FakeKafkaProducer.reset()
    monkeypatch.setattr(shared_kafka, "KafkaProducer", FakeKafkaProducer)
    monkeypatch.setattr(publisher.settings, "kafka_enabled", True)
    monkeypatch.setattr(publisher, "_START_RETRY_DELAY_SECONDS", 0.0)
    publisher._STATE.producer = None
    publisher._STATE.lock = asyncio.Lock()
    yield
    publisher._STATE.producer = None
    publisher._STATE.lock = asyncio.Lock()


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_init_event_publisher_retries_and_recovers() -> None:
    FakeKafkaProducer.start_failures = 1

    await publisher.init_event_publisher()

    assert publisher.is_event_publisher_ready() is True
    assert FakeKafkaProducer.starts == EXPECTED_RECONNECT_STARTS
    assert FakeKafkaProducer.stops == EXPECTED_STOPS


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_publish_model_event_reconnects_after_failed_send() -> None:
    FakeKafkaProducer.send_failures = 1
    event = DeliveryAssignedEvent(
        aggregate_id="assignment-1",
        order_id="order-1",
        restaurant_id="restaurant-1",
        courier_id="courier-1",
    )

    await publisher.publish_model_event(event)

    assert publisher.is_event_publisher_ready() is True
    assert FakeKafkaProducer.starts == EXPECTED_RECONNECT_STARTS
    assert FakeKafkaProducer.stops == EXPECTED_STOPS
    assert FakeKafkaProducer.sent_messages == [(event.event_type, event.aggregate_id)]
