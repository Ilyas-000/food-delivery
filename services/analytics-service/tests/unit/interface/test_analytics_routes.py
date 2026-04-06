"""Unit tests for analytics routes."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.application.dto.analytics import IngestAnalyticsEventDTO
from src.interface.dependencies.analytics import get_ingest_analytics_event_use_case
from src.main import app


async def _seed_event(event: IngestAnalyticsEventDTO) -> None:
    use_case = await get_ingest_analytics_event_use_case()
    await use_case.execute(event)


@pytest.mark.unit()
def test_get_analytics_overview_endpoint_returns_metrics() -> None:
    client = TestClient(app)

    asyncio.run(
        _seed_event(
            IngestAnalyticsEventDTO(
                event_id=uuid4(),
                event_type="order-service.order.created",
                aggregate_id="order-1",
                aggregate_type="order",
                occurred_at=datetime(2026, 4, 6, 11, 0, tzinfo=UTC),
                user_id="user-1",
                order_id="order-1",
                restaurant_id="restaurant-1",
                amount=Decimal("700.00"),
                currency="RUB",
                payload={"event_type": "order-service.order.created"},
            )
        )
    )

    response = client.get("/api/v1/analytics/overview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["orders_created"] == 1
    assert data["gross_revenue"] == "700.00"


@pytest.mark.unit()
def test_list_analytics_events_endpoint_returns_recent_items() -> None:
    client = TestClient(app)

    asyncio.run(
        _seed_event(
            IngestAnalyticsEventDTO(
                event_id=uuid4(),
                event_type="notification-service.notification.email_sent",
                aggregate_id="notification-1",
                aggregate_type="notification",
                occurred_at=datetime(2026, 4, 6, 11, 5, tzinfo=UTC),
                user_id="user-1",
                notification_type="email",
                recipient="user-1@notifications.local",
                template_name="order_created_email",
                source_event_type="order-service.order.created",
                payload={"event_type": "notification-service.notification.email_sent"},
            )
        )
    )

    response = client.get("/api/v1/analytics/events")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["event_type"] == "notification-service.notification.email_sent"


@pytest.mark.unit()
def test_get_analytics_overview_returns_422_for_invalid_range() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/analytics/overview",
        params={
            "date_from": "2026-04-07T00:00:00Z",
            "date_to": "2026-04-06T00:00:00Z",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
