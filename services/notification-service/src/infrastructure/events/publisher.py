"""Kafka-backed event publisher helpers for notification service."""

from typing import TYPE_CHECKING

import structlog

from shared.events.notification_events import (
    NotificationEmailSentEvent,
    NotificationPushSentEvent,
)
from src.config import settings
from src.domain.entities.notification import Notification

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from shared.common.kafka import KafkaProducer


class _PublisherState:
    producer: "KafkaProducer | None" = None


_STATE = _PublisherState()


async def init_event_publisher() -> None:
    """Initialize Kafka producer when enabled."""
    if not settings.kafka_enabled:
        logger.info("notification.events.kafka.disabled")
        return

    try:
        from shared.common.kafka import KafkaProducer
    except ModuleNotFoundError:
        logger.warning("notification.events.kafka.shared_module_missing")
        return

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka.bootstrap_servers,
        client_id=settings.service_name,
    )
    try:
        await producer.start()
        _STATE.producer = producer
        logger.info("notification.events.kafka.started")
    except Exception as exc:
        logger.exception("notification.events.kafka.start_failed", error=str(exc))
        _STATE.producer = None


async def shutdown_event_publisher() -> None:
    """Shutdown Kafka producer if initialized."""
    if _STATE.producer is None:
        return

    try:
        await _STATE.producer.stop()
        logger.info("notification.events.kafka.stopped")
    finally:
        _STATE.producer = None


async def publish_model_event(
    event: NotificationEmailSentEvent | NotificationPushSentEvent,
) -> None:
    """Publish notification event model."""
    if _STATE.producer is None:
        logger.debug(
            "notification.events.kafka.skip_no_producer",
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
        )
        return

    await _STATE.producer.send(event.event_type, event, key=event.aggregate_id)


def is_event_publisher_ready() -> bool:
    """Return current Kafka producer readiness state."""
    return _STATE.producer is not None


class KafkaNotificationEventPublisher:
    """Publish notification sent events to Kafka."""

    async def publish_email_sent(self, notification: Notification) -> None:
        """Publish email sent event."""
        event = NotificationEmailSentEvent(
            aggregate_id=str(notification.id),
            user_id=notification.user_id,
            notification_type=notification.notification_type.value,
            recipient=notification.recipient,
            template_name=notification.template_name,
            source_event_type=notification.event_type,
        )
        await publish_model_event(event)

    async def publish_push_sent(self, notification: Notification) -> None:
        """Publish push sent event."""
        event = NotificationPushSentEvent(
            aggregate_id=str(notification.id),
            user_id=notification.user_id,
            notification_type=notification.notification_type.value,
            recipient=notification.recipient,
            template_name=notification.template_name,
            source_event_type=notification.event_type,
        )
        await publish_model_event(event)
