"""Unit tests for payment routes."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import app


@pytest.mark.unit()
def test_reserve_payment_endpoint() -> None:
    client = TestClient(app)

    payload = {
        "order_id": str(uuid4()),
        "user_id": str(uuid4()),
        "amount": "250.00",
        "currency": "RUB",
    }

    response = client.post("/api/v1/payments/reservations", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "reserved"
    assert Decimal(data["amount"]) == Decimal("250.00")
    assert data["reservation_id"]


@pytest.mark.unit()
def test_release_payment_returns_404_for_unknown_reservation() -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/payments/reservations/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"
