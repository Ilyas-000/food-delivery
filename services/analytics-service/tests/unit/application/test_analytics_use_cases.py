"""Unit tests for analytics application layer."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.dto.analytics import IngestAnalyticsEventDTO
from src.interface.dependencies.analytics import (
    get_get_analytics_overview_use_case,
    get_ingest_analytics_event_use_case,
    get_list_analytics_events_use_case,
)

EXPECTED_LIST_TOTAL = 2
EXPECTED_OVERVIEW_TOTAL = 4


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_ingest_and_list_events_use_cases_return_recent_events() -> None:
    ingest_use_case = await get_ingest_analytics_event_use_case()
    list_use_case = await get_list_analytics_events_use_case()

    older_event = IngestAnalyticsEventDTO(
        event_id=uuid4(),
        event_type="order-service.order.created",
        aggregate_id="order-1",
        aggregate_type="order",
        occurred_at=datetime(2026, 4, 6, 9, 0, tzinfo=UTC),
        user_id="user-1",
        order_id="order-1",
        restaurant_id="restaurant-1",
        amount=Decimal("450.00"),
        currency="RUB",
        payload={"event_type": "order-service.order.created"},
    )
    newer_event = IngestAnalyticsEventDTO(
        event_id=uuid4(),
        event_type="notification-service.notification.email_sent",
        aggregate_id="notification-1",
        aggregate_type="notification",
        occurred_at=datetime(2026, 4, 6, 9, 5, tzinfo=UTC),
        user_id="user-1",
        notification_type="email",
        recipient="user-1@notifications.local",
        template_name="order_created_email",
        source_event_type="order-service.order.created",
        payload={"event_type": "notification-service.notification.email_sent"},
    )

    await ingest_use_case.execute(older_event)
    await ingest_use_case.execute(newer_event)
    result = await list_use_case.execute(event_type=None, limit=10)

    assert result.total == EXPECTED_LIST_TOTAL
    assert result.items[0].event_type == "notification-service.notification.email_sent"
    assert result.items[1].amount == Decimal("450.00")


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_overview_use_case_aggregates_metrics() -> None:
    ingest_use_case = await get_ingest_analytics_event_use_case()
    overview_use_case = await get_get_analytics_overview_use_case()

    events = [
        IngestAnalyticsEventDTO(
            event_id=uuid4(),
            event_type="order-service.order.created",
            aggregate_id="order-1",
            aggregate_type="order",
            occurred_at=datetime(2026, 4, 6, 10, 0, tzinfo=UTC),
            user_id="user-1",
            order_id="order-1",
            restaurant_id="restaurant-1",
            amount=Decimal("500.00"),
            currency="RUB",
            payload={"event_type": "order-service.order.created"},
        ),
        IngestAnalyticsEventDTO(
            event_id=uuid4(),
            event_type="order-service.order.confirmed",
            aggregate_id="order-1",
            aggregate_type="order",
            occurred_at=datetime(2026, 4, 6, 10, 2, tzinfo=UTC),
            user_id="user-1",
            order_id="order-1",
            payload={"event_type": "order-service.order.confirmed"},
        ),
        IngestAnalyticsEventDTO(
            event_id=uuid4(),
            event_type="delivery-service.delivery.assigned",
            aggregate_id="assignment-1",
            aggregate_type="delivery",
            occurred_at=datetime(2026, 4, 6, 10, 3, tzinfo=UTC),
            order_id="order-1",
            restaurant_id="restaurant-1",
            payload={"event_type": "delivery-service.delivery.assigned"},
        ),
        IngestAnalyticsEventDTO(
            event_id=uuid4(),
            event_type="notification-service.notification.push_sent",
            aggregate_id="notification-2",
            aggregate_type="notification",
            occurred_at=datetime(2026, 4, 6, 10, 4, tzinfo=UTC),
            user_id="user-1",
            notification_type="push",
            recipient="device:user-1",
            template_name="order_confirmed_push",
            source_event_type="order-service.order.confirmed",
            payload={"event_type": "notification-service.notification.push_sent"},
        ),
    ]

    for event in events:
        await ingest_use_case.execute(event)

    result = await overview_use_case.execute(date_from=None, date_to=None)

    assert result.total_events == EXPECTED_OVERVIEW_TOTAL
    assert result.orders_created == 1
    assert result.orders_confirmed == 1
    assert result.deliveries_assigned == 1
    assert result.notifications_sent == 1
    assert result.pushes_sent == 1
    assert result.gross_revenue == Decimal("500.00")
    assert result.unique_customers == 1
