"""Unit tests for analytics event processor."""

from decimal import Decimal

import pytest

from shared.events.delivery_events import DeliveryAssignedEvent
from shared.events.notification_events import NotificationEmailSentEvent
from shared.events.order_events import OrderCreatedEvent
from src.infrastructure.consumers.processor import AnalyticsEventProcessor
from src.interface.dependencies.analytics import (
    get_analytics_repository,
    get_ingest_analytics_event_use_case,
)

EXPECTED_PROCESSED_EVENTS = 3


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_event_processor_ingests_supported_events() -> None:
    repository = await get_analytics_repository()
    processor = AnalyticsEventProcessor(
        ingest_event_use_case=await get_ingest_analytics_event_use_case()
    )

    await processor.process_event(
        OrderCreatedEvent(
            aggregate_id="order-1",
            user_id="user-1",
            restaurant_id="restaurant-1",
            total_amount="650.00",
        ).model_dump(mode="json")
    )
    await processor.process_event(
        DeliveryAssignedEvent(
            aggregate_id="assignment-1",
            order_id="order-1",
            restaurant_id="restaurant-1",
        ).model_dump(mode="json")
    )
    await processor.process_event(
        NotificationEmailSentEvent(
            aggregate_id="notification-1",
            user_id="user-1",
            notification_type="email",
            recipient="user-1@notifications.local",
            template_name="order_created_email",
            source_event_type="order-service.order.created",
        ).model_dump(mode="json")
    )

    recent_events = await repository.list_events(event_type=None, limit=10)

    assert len(recent_events) == EXPECTED_PROCESSED_EVENTS
    assert recent_events[0].event_type == "notification-service.notification.email_sent"
    assert recent_events[-1].amount == Decimal("650.00")
