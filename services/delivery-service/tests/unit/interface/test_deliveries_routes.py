"""Unit tests for delivery routes."""

from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import app


@pytest.mark.unit()
def test_assign_courier_endpoint() -> None:
    client = TestClient(app)

    payload = {
        "order_id": str(uuid4()),
        "restaurant_id": str(uuid4()),
    }

    response = client.post("/api/v1/deliveries/assignments", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "assigned"
    assert data["assignment_id"]


@pytest.mark.unit()
def test_cancel_assignment_returns_404_for_unknown_assignment() -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/deliveries/assignments/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"
