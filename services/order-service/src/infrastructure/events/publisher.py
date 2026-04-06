"""Kafka-backed order event publisher."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING

import structlog

from shared.events.order_events import OrderConfirmedEvent, OrderCreatedEvent
from src.config import settings
from src.domain.entities.order import Order

logger = structlog.get_logger(__name__)

_START_MAX_ATTEMPTS = 5
_START_RETRY_DELAY_SECONDS = 2.0

if TYPE_CHECKING:
    from shared.common.kafka import KafkaProducer


class _PublisherState:
    def __init__(self) -> None:
        self.producer: KafkaProducer | None = None
        self.lock = asyncio.Lock()


_STATE = _PublisherState()


async def _stop_producer(producer: KafkaProducer) -> None:
    """Stop producer suppressing teardown errors."""
    with suppress(Exception):
        await producer.stop()


async def _build_producer() -> KafkaProducer | None:
    """Create and start Kafka producer instance."""
    if not settings.kafka_enabled:
        logger.info("order.events.kafka.disabled")
        return None

    try:
        from shared.common.kafka import KafkaProducer
    except ModuleNotFoundError:
        logger.warning("order.events.kafka.shared_module_missing")
        return None

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        client_id=settings.service_name,
    )
    try:
        await producer.start()
    except Exception as exc:
        await _stop_producer(producer)
        logger.exception("order.events.kafka.start_failed", error=str(exc))
        return None
    else:
        return producer


async def ensure_event_publisher() -> KafkaProducer | None:
    """Lazily initialize Kafka producer on startup or first publish."""
    if _STATE.producer is not None:
        return _STATE.producer

    async with _STATE.lock:
        if _STATE.producer is not None:
            return _STATE.producer

        producer = await _build_producer()
        if producer is None:
            return None

        _STATE.producer = producer
        logger.info("order.events.kafka.started")
        return producer


async def init_event_publisher() -> None:
    """Initialize Kafka producer when enabled."""
    if not settings.kafka_enabled:
        logger.info("order.events.kafka.disabled")
        return

    for attempt in range(1, _START_MAX_ATTEMPTS + 1):
        producer = await ensure_event_publisher()
        if producer is not None:
            return

        if attempt == _START_MAX_ATTEMPTS:
            logger.warning(
                "order.events.kafka.start_degraded",
                attempts=attempt,
                bootstrap_servers=settings.kafka.bootstrap_servers,
            )
            return

        logger.warning(
            "order.events.kafka.retrying_start",
            attempt=attempt,
            retry_delay_seconds=_START_RETRY_DELAY_SECONDS,
        )
        await asyncio.sleep(_START_RETRY_DELAY_SECONDS)


async def shutdown_event_publisher() -> None:
    """Shutdown Kafka producer if initialized."""
    async with _STATE.lock:
        if _STATE.producer is None:
            return

        producer = _STATE.producer
        _STATE.producer = None

    await _stop_producer(producer)
    logger.info("order.events.kafka.stopped")


async def publish_model_event(event: OrderCreatedEvent | OrderConfirmedEvent) -> None:
    """Publish order event model."""
    producer = await ensure_event_publisher()
    if producer is None:
        logger.warning(
            "order.events.kafka.skip_no_producer",
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
        )
        return

    try:
        await producer.send(event.event_type, event, key=event.aggregate_id)
    except Exception as exc:
        logger.exception(
            "order.events.kafka.publish_failed",
            error=str(exc),
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
        )

        async with _STATE.lock:
            if _STATE.producer is producer:
                _STATE.producer = None

        await _stop_producer(producer)
        retry_producer = await ensure_event_publisher()
        if retry_producer is None:
            logger.warning(
                "order.events.kafka.drop_event_no_producer",
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
            )
            return

        await retry_producer.send(event.event_type, event, key=event.aggregate_id)


def is_event_publisher_ready() -> bool:
    """Return Kafka producer readiness state."""
    return _STATE.producer is not None


class KafkaOrderEventPublisher:
    """Publish order domain events to Kafka."""

    async def publish_order_created(self, order: Order) -> None:
        """Publish order created event."""
        event = OrderCreatedEvent(
            aggregate_id=str(order.id),
            user_id=str(order.user_id),
            restaurant_id=str(order.restaurant_id),
            total_amount=order.total_amount,
        )
        await publish_model_event(event)

    async def publish_order_confirmed(self, order: Order) -> None:
        """Publish order confirmed event."""
        event = OrderConfirmedEvent(
            aggregate_id=str(order.id),
            user_id=str(order.user_id),
        )
        await publish_model_event(event)
