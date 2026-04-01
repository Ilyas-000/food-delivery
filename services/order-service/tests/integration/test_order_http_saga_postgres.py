"""Integration tests for postgres + http saga mode."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import status
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.order_model import OrderModel
from src.interface.dependencies import order as order_dependencies


async def _create_restaurant_with_menu_item() -> tuple[str, str]:
    """Create restaurant and menu item in upstream restaurant-service."""
    owner_id = str(uuid4())

    async with AsyncClient(timeout=10.0) as client:
        create_restaurant_response = await client.post(
            f"{order_dependencies.settings.restaurant_service_url}/api/v1/restaurants",
            json={
                "owner_id": owner_id,
                "name": f"Order IT Restaurant {uuid4().hex[:8]}",
                "description": "Integration test restaurant",
                "street": "Integration St. 1",
                "city": "Moscow",
                "postal_code": "101000",
                "latitude": 55.75,
                "longitude": 37.62,
                "cuisine": "russian",
            },
        )
        assert create_restaurant_response.status_code == status.HTTP_201_CREATED
        restaurant_id = create_restaurant_response.json()["id"]

        create_menu_item_response = await client.post(
            f"{order_dependencies.settings.restaurant_service_url}"
            f"/api/v1/restaurants/{restaurant_id}/menu-items",
            json={
                "name": "Borscht",
                "description": "Hot soup",
                "price_amount": "250.00",
                "category": "soup",
                "image_url": None,
            },
        )
        assert create_menu_item_response.status_code == status.HTTP_201_CREATED
        menu_item_id = create_menu_item_response.json()["id"]

    return restaurant_id, menu_item_id


@pytest.mark.integration()
async def test_create_order_persists_in_postgres_and_confirms_via_http_saga(
    order_service_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    restaurant_id, menu_item_id = await _create_restaurant_with_menu_item()
    user_id = str(uuid4())

    response = await order_service_client.post(
        "/api/v1/orders",
        json={
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "items": [
                {
                    "menu_item_id": menu_item_id,
                    "quantity": 2,
                    "unit_price": "250.00",
                    "currency": "RUB",
                }
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["status"] == "confirmed"
    assert Decimal(payload["total_amount"]) == Decimal("500.00")

    order_id = payload["id"]
    fetched = await order_service_client.get(f"/api/v1/orders/{order_id}")
    assert fetched.status_code == status.HTTP_200_OK
    assert fetched.json()["status"] == "confirmed"

    stored_order = await db_session.get(OrderModel, UUID(order_id))
    assert stored_order is not None
    assert stored_order.status.value == "confirmed"
    assert Decimal(str(stored_order.total_amount)) == Decimal("500.00")


@pytest.mark.integration()
async def test_create_order_marks_cancelled_when_delivery_step_fails(
    order_service_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant_id, menu_item_id = await _create_restaurant_with_menu_item()
    user_id = str(uuid4())

    monkeypatch.setattr(order_dependencies.settings, "delivery_service_url", "http://127.0.0.1:9")

    response = await order_service_client.post(
        "/api/v1/orders",
        json={
            "user_id": user_id,
            "restaurant_id": restaurant_id,
            "items": [
                {
                    "menu_item_id": menu_item_id,
                    "quantity": 1,
                    "unit_price": "250.00",
                    "currency": "RUB",
                }
            ],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_payload = response.json()["error"]
    assert error_payload["code"] == "BUSINESS_RULE_VIOLATION"
    assert "assign_courier" in error_payload["message"]

    result = await db_session.execute(
        select(OrderModel)
        .where(OrderModel.user_id == UUID(user_id))
        .order_by(OrderModel.created_at.desc())
    )
    failed_order = result.scalar_one()
    assert failed_order.status.value == "cancelled"
    assert failed_order.cancellation_reason == "saga_failed"
