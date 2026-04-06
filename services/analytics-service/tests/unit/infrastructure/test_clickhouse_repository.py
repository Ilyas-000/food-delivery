"""Unit tests for ClickHouse analytics repository."""

from datetime import UTC, datetime
from decimal import Decimal
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities.analytics_event import AnalyticsEvent
from src.infrastructure.repositories.clickhouse_analytics_repository import (
    ClickHouseAnalyticsRepository,
)


def _response(text: str = "") -> MagicMock:
    response = MagicMock()
    response.text = text
    response.raise_for_status = MagicMock()
    return response


def _build_repository() -> ClickHouseAnalyticsRepository:
    return ClickHouseAnalyticsRepository(
        host="clickhouse",
        http_port=8123,
        user="default",
        password="",
        database="analytics_db",
        table="analytics_events",
        timeout_seconds=5.0,
    )


def _build_event() -> AnalyticsEvent:
    return AnalyticsEvent.create(
        event_id=uuid4(),
        event_type="order-service.order.created",
        aggregate_id="order-1",
        aggregate_type="order",
        occurred_at=datetime(2026, 4, 6, 12, 0, tzinfo=UTC),
        user_id="user-1",
        order_id="order-1",
        restaurant_id="restaurant-1",
        amount=Decimal("800.00"),
        currency="RUB",
        payload={"event_type": "order-service.order.created"},
    )


def _list_row_response() -> str:
    return json.dumps(
        {
            "event_id": "00000000-0000-0000-0000-000000000001",
            "event_type": "order-service.order.created",
            "aggregate_id": "order-1",
            "aggregate_type": "order",
            "occurred_at": "2026-04-06 12:00:00.000",
            "user_id": "user-1",
            "order_id": "order-1",
            "restaurant_id": "restaurant-1",
            "amount": 800.0,
            "currency": "RUB",
            "notification_type": None,
            "recipient": None,
            "template_name": None,
            "source_event_type": None,
            "payload_json": json.dumps({"event_type": "order-service.order.created"}),
        }
    )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_clickhouse_repository_start_save_query_and_stop() -> None:
    client = AsyncMock()
    client.post = AsyncMock(
        side_effect=[
            _response(),
            _response(),
            _response(),
            _response(),
            _response(f"{_list_row_response()}\n"),
            _response(
                '{"total_events":1,"orders_created":1,"orders_confirmed":0,"deliveries_assigned":0,"emails_sent":0,"pushes_sent":0,"gross_revenue":800.0,"unique_customers":1}\n'
            ),
        ]
    )
    client.aclose = AsyncMock()

    repository = _build_repository()

    with patch(
        "src.infrastructure.repositories.clickhouse_analytics_repository.httpx.AsyncClient",
        return_value=client,
    ):
        await repository.start()
        saved = await repository.save(_build_event())
        listed = await repository.list_events(event_type="order-service.order.created", limit=10)
        overview = await repository.get_overview(
            date_from=datetime(2026, 4, 6, 0, 0, tzinfo=UTC),
            date_to=datetime(2026, 4, 6, 23, 59, tzinfo=UTC),
        )
        await repository.stop()

    assert repository.is_ready() is False
    assert saved.amount == Decimal("800.00")
    assert len(listed) == 1
    assert listed[0].amount == Decimal("800.0")
    assert overview.orders_created == 1
    assert overview.gross_revenue == Decimal("800.00")
    first_call = client.post.await_args_list[0]
    assert first_call.kwargs["params"] == {}
    assert first_call.kwargs["content"] == "CREATE DATABASE IF NOT EXISTS analytics_db"
    insert_call = client.post.await_args_list[3]
    assert insert_call.kwargs["params"]["query"].startswith(
        "INSERT INTO analytics_db.analytics_events"
    )
    client.aclose.assert_awaited_once()
