"""Unit tests for HTTP service clients used by order saga."""

from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from src.domain.exceptions.order import InvalidOrderDataError
from src.domain.value_objects.order_item import OrderItem
from src.infrastructure.clients.http_service_clients import (
    DeliveryServiceHttpClient,
    PaymentServiceHttpClient,
    RestaurantServiceHttpClient,
)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_restaurant_client_validates_item_successfully() -> None:
    restaurant_id = uuid4()
    menu_item_id = uuid4()
    item = OrderItem(menu_item_id=menu_item_id, quantity=2, unit_price=Decimal("100.00"))

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/api/v1/restaurants/{restaurant_id}/menu-items/{menu_item_id}"
        return httpx.Response(
            status_code=200,
            json={
                "id": str(menu_item_id),
                "availability": "available",
                "price_amount": "100.00",
                "price_currency": "RUB",
            },
        )

    client = RestaurantServiceHttpClient(
        base_url="http://restaurant-service:8002",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    await client.validate_items(restaurant_id=restaurant_id, items=(item,))


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_restaurant_client_raises_for_unavailable_item() -> None:
    restaurant_id = uuid4()
    menu_item_id = uuid4()
    item = OrderItem(menu_item_id=menu_item_id, quantity=1, unit_price=Decimal("99.90"))

    client = RestaurantServiceHttpClient(
        base_url="http://restaurant-service:8002",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                status_code=200,
                json={
                    "id": str(menu_item_id),
                    "availability": "out_of_stock",
                    "price_amount": "99.90",
                    "price_currency": "RUB",
                },
            )
        ),
    )

    with pytest.raises(InvalidOrderDataError, match="not available"):
        await client.validate_items(restaurant_id=restaurant_id, items=(item,))


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_restaurant_client_raises_for_price_mismatch() -> None:
    restaurant_id = uuid4()
    menu_item_id = uuid4()
    item = OrderItem(menu_item_id=menu_item_id, quantity=1, unit_price=Decimal("100.00"))

    client = RestaurantServiceHttpClient(
        base_url="http://restaurant-service:8002",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                status_code=200,
                json={
                    "id": str(menu_item_id),
                    "availability": "available",
                    "price_amount": "105.00",
                    "price_currency": "RUB",
                },
            )
        ),
    )

    with pytest.raises(InvalidOrderDataError, match="outdated price"):
        await client.validate_items(restaurant_id=restaurant_id, items=(item,))


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_payment_client_reserve_and_release_success() -> None:
    reservation_id = str(uuid4())
    order_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.headers.get("Idempotency-Key") == str(order_id)
            return httpx.Response(status_code=201, json={"reservation_id": reservation_id})
        return httpx.Response(status_code=204)

    client = PaymentServiceHttpClient(
        base_url="http://payment-service:8004",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = await client.reserve(
        order_id=order_id,
        user_id=uuid4(),
        amount=Decimal("450.00"),
        currency="RUB",
    )
    assert result == reservation_id

    await client.release(reservation_id)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_delivery_client_assign_and_cancel_success() -> None:
    assignment_id = str(uuid4())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(status_code=201, json={"assignment_id": assignment_id})
        return httpx.Response(status_code=204)

    client = DeliveryServiceHttpClient(
        base_url="http://delivery-service:8005",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = await client.assign(order_id=uuid4(), restaurant_id=uuid4())
    assert result == assignment_id

    await client.cancel(assignment_id)
