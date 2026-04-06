"""Integration tests for analytics reporting against ClickHouse."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
import pytest

from shared.events.notification_events import NotificationEmailSentEvent
from shared.events.order_events import OrderCreatedEvent
from src.application.dto.analytics import IngestAnalyticsEventDTO
from src.infrastructure.consumers.processor import AnalyticsEventProcessor
from src.interface.dependencies.analytics import get_ingest_analytics_event_use_case


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_clickhouse_overview_endpoint_returns_aggregated_metrics(
    analytics_service_client: AsyncClient,
) -> None:
    ingest_use_case = await get_ingest_analytics_event_use_case()
    await ingest_use_case.execute(
        IngestAnalyticsEventDTO(
            event_id=uuid4(),
            event_type="order-service.order.created",
            aggregate_id="order-1",
            aggregate_type="order",
            occurred_at=datetime(2026, 4, 6, 12, 0, tzinfo=UTC),
            user_id="user-1",
            order_id="order-1",
            restaurant_id="restaurant-1",
            amount=Decimal("990.00"),
            currency="RUB",
            payload={"event_type": "order-service.order.created"},
        )
    )

    response = await analytics_service_client.get("/api/v1/analytics/overview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["orders_created"] == 1
    assert data["gross_revenue"] == "990.00"
    assert data["unique_customers"] == 1


@pytest.mark.asyncio()
@pytest.mark.integration()
async def test_clickhouse_events_endpoint_returns_records_ingested_by_processor(
    analytics_service_client: AsyncClient,
) -> None:
    processor = AnalyticsEventProcessor(
        ingest_event_use_case=await get_ingest_analytics_event_use_case()
    )

    await processor.process_event(
        OrderCreatedEvent(
            aggregate_id="order-42",
            user_id="user-42",
            restaurant_id="restaurant-42",
            total_amount="1200.00",
        ).model_dump(mode="json")
    )
    await processor.process_event(
        NotificationEmailSentEvent(
            aggregate_id="notification-42",
            user_id="user-42",
            notification_type="email",
            recipient="user-42@notifications.local",
            template_name="order_created_email",
            source_event_type="order-service.order.created",
        ).model_dump(mode="json")
    )

    response = await analytics_service_client.get(
        "/api/v1/analytics/events",
        params={"event_type": "notification-service.notification.email_sent"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["recipient"] == "user-42@notifications.local"
