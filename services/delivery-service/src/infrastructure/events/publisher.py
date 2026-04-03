"""Kafka-backed event publisher helpers."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from shared.common.kafka import KafkaProducer


class _PublisherState:
    producer: "KafkaProducer | None" = None


_STATE = _PublisherState()


async def init_event_publisher() -> None:
    """Initialize Kafka producer when enabled."""
    if not settings.kafka_enabled:
        logger.info("events.kafka.disabled")
        return

    try:
        from shared.common.kafka import KafkaProducer
    except ModuleNotFoundError:
        logger.warning("events.kafka.shared_module_missing")
        return

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        client_id=settings.service_name,
    )

    try:
        await producer.start()
        _STATE.producer = producer
        logger.info("events.kafka.started", bootstrap_servers=settings.kafka.bootstrap_servers)
    except Exception as exc:
        logger.exception("events.kafka.start_failed", error=str(exc))
        _STATE.producer = None


async def shutdown_event_publisher() -> None:
    """Shutdown Kafka producer if initialized."""
    if _STATE.producer is None:
        return

    try:
        await _STATE.producer.stop()
        logger.info("events.kafka.stopped")
    finally:
        _STATE.producer = None


async def publish_event(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    user_id: str | None = None,
) -> None:
    """Publish domain event to Kafka topic."""
    if _STATE.producer is None:
        logger.debug(
            "events.kafka.skip_no_producer",
            event_type=event_type,
            aggregate_id=aggregate_id,
        )
        return

    message = {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "aggregate_id": aggregate_id,
        "aggregate_type": aggregate_type,
        "occurred_at": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "payload": payload,
    }
    await _STATE.producer.send(event_type, message, key=aggregate_id)


def is_event_publisher_ready() -> bool:
    """Return current Kafka producer readiness state."""
    return _STATE.producer is not None
