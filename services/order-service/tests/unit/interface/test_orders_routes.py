"""Unit tests for order routes."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import app


@pytest.mark.unit()
def test_create_order_endpoint() -> None:
    client = TestClient(app)

    payload = {
        "user_id": str(uuid4()),
        "restaurant_id": str(uuid4()),
        "items": [
            {
                "menu_item_id": str(uuid4()),
                "quantity": 2,
                "unit_price": "100.00",
                "currency": "RUB",
            }
        ],
    }

    response = client.post("/api/v1/orders", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "confirmed"
    assert Decimal(data["total_amount"]) == Decimal("200.00")


@pytest.mark.unit()
def test_get_order_endpoint_returns_404_for_unknown_id() -> None:
    client = TestClient(app)

    response = client.get(f"/api/v1/orders/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"
