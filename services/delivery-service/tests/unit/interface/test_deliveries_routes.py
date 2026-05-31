"""Unit tests for delivery routes."""

from collections.abc import Iterator
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.infrastructure.repositories.in_memory_assignment_repository import (
    InMemoryAssignmentRepository,
)
from src.interface.dependencies.database import get_assignment_repository
from src.main import app


@pytest.fixture(autouse=True)
def _use_in_memory_repository() -> Iterator[None]:
    """Route unit tests run against an in-memory repository, not PostgreSQL."""
    repository = InMemoryAssignmentRepository()

    async def override() -> IAssignmentRepository:
        return repository

    app.dependency_overrides[get_assignment_repository] = override
    yield
    app.dependency_overrides.pop(get_assignment_repository, None)


def _assignment_payload(order_id: str | None = None) -> dict[str, str]:
    return {
        "order_id": order_id or str(uuid4()),
        "restaurant_id": str(uuid4()),
        "courier_id": str(uuid4()),
    }


@pytest.mark.unit()
def test_assign_courier_endpoint() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/deliveries/assignments", json=_assignment_payload())

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "assigned"
    assert data["assignment_id"]
    assert data["courier_id"]


@pytest.mark.unit()
def test_cancel_assignment_returns_404_for_unknown_assignment() -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/deliveries/assignments/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.unit()
def test_get_assignment_by_order_endpoint() -> None:
    client = TestClient(app)

    order_id = str(uuid4())
    assign_response = client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )
    assert assign_response.status_code == status.HTTP_201_CREATED

    response = client.get(f"/api/v1/deliveries/orders/{order_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["order_id"] == order_id
    assert response.json()["courier_id"]


@pytest.mark.unit()
def test_update_location_endpoint_broadcasts_websocket_event() -> None:
    client = TestClient(app)

    order_id = str(uuid4())
    assign_response = client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )
    assert assign_response.status_code == status.HTTP_201_CREATED

    with client.websocket_connect(f"/ws/orders/{order_id}") as websocket:
        response = client.post(
            "/api/v1/deliveries/location",
            json={
                "order_id": order_id,
                "latitude": 55.7558,
                "longitude": 37.6173,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["status"] == "in_transit"
        assert body["latitude"] == pytest.approx(55.7558)
        assert body["longitude"] == pytest.approx(37.6173)

        event = websocket.receive_json()
        assert event["type"] == "location_update"
        assert event["data"]["order_id"] == order_id
        assert event["data"]["status"] == "in_transit"
        assert event["data"]["latitude"] == pytest.approx(55.7558)
        assert event["data"]["longitude"] == pytest.approx(37.6173)


@pytest.mark.unit()
def test_complete_delivery_endpoint_updates_status() -> None:
    client = TestClient(app)

    order_id = str(uuid4())
    assign_response = client.post(
        "/api/v1/deliveries/assignments",
        json=_assignment_payload(order_id),
    )
    assert assign_response.status_code == status.HTTP_201_CREATED

    response = client.post(f"/api/v1/deliveries/{order_id}/complete")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "completed"
    assert body["delivered_at"] is not None


@pytest.mark.unit()
def test_update_location_returns_404_for_unknown_order() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/deliveries/location",
        json={
            "order_id": str(uuid4()),
            "latitude": 55.7558,
            "longitude": 37.6173,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.unit()
def test_cancel_completed_assignment_returns_422() -> None:
    client = TestClient(app)

    assign_response = client.post("/api/v1/deliveries/assignments", json=_assignment_payload())
    assignment_id = assign_response.json()["assignment_id"]
    order_id = assign_response.json()["order_id"]

    complete_response = client.post(f"/api/v1/deliveries/{order_id}/complete")
    assert complete_response.status_code == status.HTTP_200_OK

    response = client.delete(f"/api/v1/deliveries/assignments/{assignment_id}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
