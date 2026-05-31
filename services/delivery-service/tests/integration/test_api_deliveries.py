"""Integration tests for delivery assignment persistence."""

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
import pytest


def _assignment_payload(order_id: str | None = None) -> dict[str, str]:
    return {
        "order_id": order_id or str(uuid4()),
        "restaurant_id": str(uuid4()),
        "courier_id": str(uuid4()),
    }


@pytest.mark.integration()
async def test_assignment_is_persisted_and_retrievable(
    delivery_service_client: AsyncClient,
) -> None:
    order_id = str(uuid4())

    create_response = await delivery_service_client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    get_response = await delivery_service_client.get(f"/api/v1/deliveries/orders/{order_id}")
    assert get_response.status_code == status.HTTP_200_OK
    body = get_response.json()
    assert body["order_id"] == order_id
    assert body["status"] == "assigned"
    assert body["assignment_id"] == create_response.json()["assignment_id"]


@pytest.mark.integration()
async def test_location_update_persists_current_location(
    delivery_service_client: AsyncClient,
) -> None:
    order_id = str(uuid4())
    await delivery_service_client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )

    update_response = await delivery_service_client.post(
        "/api/v1/deliveries/location",
        json={"order_id": order_id, "latitude": 55.7558, "longitude": 37.6173},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()["status"] == "in_transit"

    get_response = await delivery_service_client.get(f"/api/v1/deliveries/orders/{order_id}")
    body = get_response.json()
    assert body["status"] == "in_transit"
    assert body["latitude"] == pytest.approx(55.7558)
    assert body["longitude"] == pytest.approx(37.6173)


@pytest.mark.integration()
async def test_complete_delivery_persists_terminal_state(
    delivery_service_client: AsyncClient,
) -> None:
    order_id = str(uuid4())
    await delivery_service_client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )

    complete_response = await delivery_service_client.post(
        f"/api/v1/deliveries/{order_id}/complete",
    )
    assert complete_response.status_code == status.HTTP_200_OK

    get_response = await delivery_service_client.get(f"/api/v1/deliveries/orders/{order_id}")
    body = get_response.json()
    assert body["status"] == "completed"
    assert body["delivered_at"] is not None
