"""Repository-level end-to-end order journey scenarios."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal
import os
from typing import Any
from uuid import uuid4

from fastapi import status
import httpx
import pytest

EXPECTED_ORDER_EMAIL_TEMPLATES = {
    "order_created_email",
    "order_confirmed_email",
    "courier_assigned_email",
}
EXPECTED_ORDER_PUSH_TEMPLATES = {
    "order_confirmed_push",
    "courier_assigned_push",
}
DEFAULT_CONCURRENT_ORDERS = 10


@dataclass(frozen=True)
class ServiceEndpoints:
    """Resolved base URLs for live e2e services."""

    gateway: str
    delivery: str
    notification: str


@dataclass(frozen=True)
class UserSession:
    """Authenticated customer session used in e2e tests."""

    user_id: str
    email: str
    password: str
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class MenuSetup:
    """Restaurant + menu item test fixture data."""

    restaurant_id: str
    menu_item_id: str
    price_amount: str


@pytest.fixture()
def service_endpoints() -> ServiceEndpoints:
    """Resolve service base URLs for Docker-backed e2e tests."""
    return ServiceEndpoints(
        gateway=os.getenv("E2E_GATEWAY_URL", "http://api-gateway:8000").rstrip("/"),
        delivery=os.getenv("E2E_DELIVERY_SERVICE_URL", "http://delivery-service:8005").rstrip("/"),
        notification=os.getenv(
            "E2E_NOTIFICATION_SERVICE_URL",
            "http://notification-service:8006",
        ).rstrip("/"),
    )


@pytest.fixture()
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    """Shared HTTP client for e2e scenarios."""
    timeout_seconds = float(os.getenv("E2E_HTTP_TIMEOUT_SECONDS", "20.0"))
    async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=False) as client:
        yield client


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _register_and_login(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
) -> UserSession:
    email = f"e2e-{uuid4()}@example.com"
    password = "SecurePass123!"

    register_response = await client.post(
        f"{endpoints.gateway}/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "E2E Customer"},
    )
    assert register_response.status_code == status.HTTP_201_CREATED, register_response.text

    login_response = await client.post(
        f"{endpoints.gateway}/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK, login_response.text
    login_payload = login_response.json()

    profile_response = await client.get(
        f"{endpoints.gateway}/api/v1/users/me",
        headers=_auth_headers(login_payload["access_token"]),
    )
    assert profile_response.status_code == status.HTTP_200_OK, profile_response.text
    profile_payload = profile_response.json()

    return UserSession(
        user_id=profile_payload["id"],
        email=email,
        password=password,
        access_token=login_payload["access_token"],
        refresh_token=login_payload["refresh_token"],
    )


async def _create_restaurant_with_menu_item(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
    *,
    price_amount: str = "349.00",
) -> MenuSetup:
    create_restaurant_response = await client.post(
        f"{endpoints.gateway}/api/v1/restaurants",
        headers=_auth_headers(session.access_token),
        json={
            "owner_id": session.user_id,
            "name": f"Journey Restaurant {uuid4().hex[:8]}",
            "description": "End-to-end order journey restaurant",
            "street": "Integration Street 9",
            "city": "Moscow",
            "postal_code": "101000",
            "latitude": 55.7558,
            "longitude": 37.6173,
            "cuisine": "italian",
        },
    )
    assert create_restaurant_response.status_code == status.HTTP_201_CREATED
    restaurant_id = create_restaurant_response.json()["id"]

    create_menu_item_response = await client.post(
        f"{endpoints.gateway}/api/v1/restaurants/{restaurant_id}/menu-items",
        headers=_auth_headers(session.access_token),
        json={
            "name": "Journey Pasta",
            "description": "Fresh pasta for e2e flow",
            "price_amount": price_amount,
            "category": "main_course",
            "image_url": None,
        },
    )
    assert create_menu_item_response.status_code == status.HTTP_201_CREATED
    menu_item_id = create_menu_item_response.json()["id"]

    return MenuSetup(
        restaurant_id=restaurant_id,
        menu_item_id=menu_item_id,
        price_amount=price_amount,
    )


async def _create_order(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
    menu_setup: MenuSetup,
) -> dict[str, Any]:
    response = await client.post(
        f"{endpoints.gateway}/api/v1/orders",
        headers=_auth_headers(session.access_token),
        json={
            "user_id": session.user_id,
            "restaurant_id": menu_setup.restaurant_id,
            "items": [
                {
                    "menu_item_id": menu_setup.menu_item_id,
                    "quantity": 1,
                    "unit_price": menu_setup.price_amount,
                    "currency": "RUB",
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


async def _create_order_with_quantity(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
    menu_setup: MenuSetup,
    *,
    quantity: int,
) -> dict[str, Any]:
    response = await client.post(
        f"{endpoints.gateway}/api/v1/orders",
        headers=_auth_headers(session.access_token),
        json={
            "user_id": session.user_id,
            "restaurant_id": menu_setup.restaurant_id,
            "items": [
                {
                    "menu_item_id": menu_setup.menu_item_id,
                    "quantity": quantity,
                    "unit_price": menu_setup.price_amount,
                    "currency": "RUB",
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


async def _get_payment_history(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
    *,
    order_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    params: dict[str, str] = {}
    if order_id is not None:
        params["order_id"] = order_id
    if user_id is not None:
        params["user_id"] = user_id

    response = await client.get(
        f"{endpoints.gateway}/api/v1/payments/history",
        headers=_auth_headers(session.access_token),
        params=params,
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _get_delivery_assignment(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    order_id: str,
) -> dict[str, Any]:
    response = await client.get(f"{endpoints.delivery}/api/v1/deliveries/orders/{order_id}")
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _list_notifications(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
) -> dict[str, Any]:
    response = await client.get(f"{endpoints.notification}/api/v1/notifications")
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _get_analytics_overview(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
) -> dict[str, Any]:
    response = await client.get(
        f"{endpoints.gateway}/api/v1/analytics/overview",
        headers=_auth_headers(session.access_token),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _list_analytics_events(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    session: UserSession,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    response = await client.get(
        f"{endpoints.gateway}/api/v1/analytics/events",
        headers=_auth_headers(session.access_token),
        params={"limit": limit},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _get_courier_rating(
    client: httpx.AsyncClient,
    endpoints: ServiceEndpoints,
    courier_id: str,
) -> dict[str, Any]:
    response = await client.get(f"{endpoints.gateway}/api/v1/reviews/couriers/{courier_id}/rating")
    assert response.status_code == status.HTTP_200_OK, response.text
    return response.json()


async def _wait_until(
    description: str,
    loader: Any,
    predicate: Any,
    *,
    attempts: int = 30,
    delay_seconds: float = 1.0,
) -> Any:
    last_value: Any = None
    for _ in range(attempts):
        last_value = await loader()
        if predicate(last_value):
            return last_value
        await asyncio.sleep(delay_seconds)

    pytest.fail(f"Timed out waiting for {description}. Last value: {last_value}")


@pytest.mark.asyncio()
@pytest.mark.e2e()
async def test_order_happy_path_produces_runtime_side_effects(
    http_client: httpx.AsyncClient,
    service_endpoints: ServiceEndpoints,
) -> None:
    """Run the contract-stage happy path across gateway, saga, notifications, and analytics."""
    session = await _register_and_login(http_client, service_endpoints)
    menu_setup = await _create_restaurant_with_menu_item(http_client, service_endpoints, session)
    overview_before = await _get_analytics_overview(http_client, service_endpoints, session)

    order_payload = await _create_order(http_client, service_endpoints, session, menu_setup)
    order_id = order_payload["id"]

    assert order_payload["status"] == "confirmed"
    assert Decimal(order_payload["total_amount"]) == Decimal(menu_setup.price_amount)

    payment_history = await _get_payment_history(
        http_client,
        service_endpoints,
        session,
        order_id=order_id,
    )
    assert payment_history["total"] == 1
    payment = payment_history["items"][0]
    assert payment["order_id"] == order_id
    assert payment["status"] == "pending"

    assignment_before_delivery = await _get_delivery_assignment(
        http_client,
        service_endpoints,
        order_id,
    )
    assignment_id = assignment_before_delivery["assignment_id"]
    courier_id = assignment_before_delivery["courier_id"]
    assert assignment_before_delivery["status"] == "assigned"

    update_location_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/deliveries/location",
        headers=_auth_headers(session.access_token),
        json={"order_id": order_id, "latitude": 55.751244, "longitude": 37.618423},
    )
    assert update_location_response.status_code == status.HTTP_200_OK, update_location_response.text
    assert update_location_response.json()["status"] == "in_transit"

    complete_delivery_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/deliveries/{order_id}/complete",
        headers=_auth_headers(session.access_token),
    )
    assert (
        complete_delivery_response.status_code == status.HTTP_200_OK
    ), complete_delivery_response.text
    assert complete_delivery_response.json()["status"] == "completed"

    notifications = await _wait_until(
        "notification fan-out for order happy path",
        lambda: _list_notifications(http_client, service_endpoints),
        lambda payload: {
            item["template_name"]
            for item in payload["items"]
            if item["user_id"] == session.user_id
            and item["aggregate_id"] in {order_id, assignment_id}
        }
        >= EXPECTED_ORDER_EMAIL_TEMPLATES | EXPECTED_ORDER_PUSH_TEMPLATES,
    )
    templates = {
        item["template_name"]
        for item in notifications["items"]
        if item["user_id"] == session.user_id and item["aggregate_id"] in {order_id, assignment_id}
    }
    assert templates >= EXPECTED_ORDER_EMAIL_TEMPLATES
    assert templates >= EXPECTED_ORDER_PUSH_TEMPLATES

    analytics_overview = await _wait_until(
        "analytics counters for happy path",
        lambda: _get_analytics_overview(http_client, service_endpoints, session),
        lambda payload: (
            payload["orders_created"] >= overview_before["orders_created"] + 1
            and payload["orders_confirmed"] >= overview_before["orders_confirmed"] + 1
            and payload["deliveries_assigned"] >= overview_before["deliveries_assigned"] + 1
            and payload["emails_sent"] >= overview_before["emails_sent"] + 3
            and payload["pushes_sent"] >= overview_before["pushes_sent"] + 2
        ),
    )
    assert analytics_overview["notifications_sent"] >= analytics_overview["emails_sent"]

    analytics_events = await _wait_until(
        "analytics events for created/confirmed/assigned flow",
        lambda: _list_analytics_events(http_client, service_endpoints, session),
        lambda payload: {
            (item["event_type"], item.get("aggregate_id"), item.get("order_id"))
            for item in payload["items"]
        }
        >= {
            ("order-service.order.created", order_id, order_id),
            ("order-service.order.confirmed", order_id, order_id),
            ("delivery-service.delivery.assigned", assignment_id, order_id),
        },
    )
    observed_events = {
        (item["event_type"], item.get("aggregate_id"), item.get("order_id"))
        for item in analytics_events["items"]
    }
    assert ("order-service.order.created", order_id, order_id) in observed_events
    assert ("order-service.order.confirmed", order_id, order_id) in observed_events
    assert ("delivery-service.delivery.assigned", assignment_id, order_id) in observed_events
    assert courier_id


@pytest.mark.asyncio()
@pytest.mark.e2e()
@pytest.mark.slow()
async def test_order_creation_remains_stable_under_concurrent_load(
    http_client: httpx.AsyncClient,
    service_endpoints: ServiceEndpoints,
) -> None:
    """Create multiple orders in parallel and verify the saga stays stable."""
    if os.getenv("RUN_E2E_LOAD") != "1":
        pytest.skip("Load smoke is opt-in. Run with RUN_E2E_LOAD=1.")

    session = await _register_and_login(http_client, service_endpoints)
    menu_setup = await _create_restaurant_with_menu_item(http_client, service_endpoints, session)
    concurrency = int(os.getenv("E2E_CONCURRENT_ORDERS", str(DEFAULT_CONCURRENT_ORDERS)))

    orders = await asyncio.gather(
        *[
            _create_order_with_quantity(
                http_client,
                service_endpoints,
                session,
                menu_setup,
                quantity=index % 3 + 1,
            )
            for index in range(concurrency)
        ]
    )

    assert len({order["id"] for order in orders}) == concurrency
    assert all(order["status"] == "confirmed" for order in orders)

    payment_history = await _get_payment_history(
        http_client,
        service_endpoints,
        session,
        user_id=session.user_id,
    )
    assert payment_history["total"] == concurrency

    for order in orders[:5]:
        assignment = await _get_delivery_assignment(
            http_client,
            service_endpoints,
            order["id"],
        )
        assert assignment["status"] == "assigned"


@pytest.mark.asyncio()
@pytest.mark.e2e()
async def test_order_rejects_out_of_stock_menu_items_without_payment(
    http_client: httpx.AsyncClient,
    service_endpoints: ServiceEndpoints,
) -> None:
    """Unavailable menu items must fail before payment reservation is created."""
    session = await _register_and_login(http_client, service_endpoints)
    menu_setup = await _create_restaurant_with_menu_item(http_client, service_endpoints, session)

    update_availability_response = await http_client.patch(
        f"{service_endpoints.gateway}/api/v1/restaurants/{menu_setup.restaurant_id}"
        f"/menu-items/{menu_setup.menu_item_id}/availability",
        headers=_auth_headers(session.access_token),
        json={"availability": "out_of_stock"},
    )
    assert (
        update_availability_response.status_code == status.HTTP_200_OK
    ), update_availability_response.text

    create_order_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/orders",
        headers=_auth_headers(session.access_token),
        json={
            "user_id": session.user_id,
            "restaurant_id": menu_setup.restaurant_id,
            "items": [
                {
                    "menu_item_id": menu_setup.menu_item_id,
                    "quantity": 1,
                    "unit_price": menu_setup.price_amount,
                    "currency": "RUB",
                }
            ],
        },
    )
    assert (
        create_order_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), create_order_response.text
    error_payload = create_order_response.json()["error"]
    assert error_payload["code"] == "BUSINESS_RULE_VIOLATION"
    assert "not available" in error_payload["message"]

    payment_history = await _get_payment_history(
        http_client,
        service_endpoints,
        session,
        user_id=session.user_id,
    )
    assert payment_history["total"] == 0


@pytest.mark.asyncio()
@pytest.mark.e2e()
async def test_review_flow_requires_completed_delivery_and_updates_summaries(
    http_client: httpx.AsyncClient,
    service_endpoints: ServiceEndpoints,
) -> None:
    """Review validation must depend on real order ownership and completed delivery state."""
    session = await _register_and_login(http_client, service_endpoints)
    menu_setup = await _create_restaurant_with_menu_item(http_client, service_endpoints, session)
    order_payload = await _create_order(http_client, service_endpoints, session, menu_setup)
    order_id = order_payload["id"]

    assignment_before_completion = await _get_delivery_assignment(
        http_client,
        service_endpoints,
        order_id,
    )
    courier_id = assignment_before_completion["courier_id"]
    courier_rating_before = await _get_courier_rating(http_client, service_endpoints, courier_id)
    previous_courier_reviews_count = int(courier_rating_before["reviews_count"])
    previous_courier_average = Decimal(courier_rating_before["average_rating"])

    create_restaurant_review_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/reviews",
        headers=_auth_headers(session.access_token),
        json={
            "order_id": order_id,
            "target_type": "restaurant",
            "target_id": menu_setup.restaurant_id,
            "rating": 5,
            "comment": "Will wait for delivery completion first.",
        },
    )
    assert (
        create_restaurant_review_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ), create_restaurant_review_response.text
    assert "delivery completion" in create_restaurant_review_response.json()["error"]["message"]

    complete_delivery_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/deliveries/{order_id}/complete",
        headers=_auth_headers(session.access_token),
    )
    assert (
        complete_delivery_response.status_code == status.HTTP_200_OK
    ), complete_delivery_response.text

    restaurant_review_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/reviews",
        headers=_auth_headers(session.access_token),
        json={
            "order_id": order_id,
            "target_type": "restaurant",
            "target_id": menu_setup.restaurant_id,
            "rating": 5,
            "comment": "Excellent delivery and food.",
        },
    )
    assert restaurant_review_response.status_code == status.HTTP_201_CREATED
    assert restaurant_review_response.json()["target_type"] == "restaurant"

    courier_review_response = await http_client.post(
        f"{service_endpoints.gateway}/api/v1/reviews",
        headers=_auth_headers(session.access_token),
        json={
            "order_id": order_id,
            "target_type": "courier",
            "target_id": courier_id,
            "rating": 4,
            "comment": "Courier was fast and careful.",
        },
    )
    assert courier_review_response.status_code == status.HTTP_201_CREATED
    assert courier_review_response.json()["target_type"] == "courier"

    restaurant_rating_response = await http_client.get(
        f"{service_endpoints.gateway}/api/v1/reviews/restaurants/{menu_setup.restaurant_id}/rating",
    )
    assert restaurant_rating_response.status_code == status.HTTP_200_OK
    restaurant_rating = restaurant_rating_response.json()
    assert restaurant_rating["reviews_count"] == 1
    assert restaurant_rating["average_rating"] == "5.00"

    courier_rating_response = await http_client.get(
        f"{service_endpoints.gateway}/api/v1/reviews/couriers/{courier_id}/rating",
    )
    assert courier_rating_response.status_code == status.HTTP_200_OK
    courier_rating = courier_rating_response.json()
    assert courier_rating["reviews_count"] == previous_courier_reviews_count + 1

    expected_courier_average = (
        previous_courier_average * previous_courier_reviews_count + Decimal("4.00")
    ) / Decimal(previous_courier_reviews_count + 1)
    assert Decimal(courier_rating["average_rating"]) == expected_courier_average.quantize(
        Decimal("0.01")
    )
