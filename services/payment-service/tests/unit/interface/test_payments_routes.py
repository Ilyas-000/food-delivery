"""Unit tests for payment routes."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import app


def _reserve_payload() -> dict[str, str]:
    return {
        "order_id": str(uuid4()),
        "user_id": str(uuid4()),
        "amount": "250.00",
        "currency": "RUB",
    }


@pytest.mark.unit()
def test_reserve_payment_endpoint() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/payments/reservations", json=_reserve_payload())

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "reserved"
    assert Decimal(data["amount"]) == Decimal("250.00")
    assert data["reservation_id"]


@pytest.mark.unit()
def test_reserve_payment_with_same_idempotency_key_returns_same_payment() -> None:
    client = TestClient(app)

    payload = _reserve_payload()
    idempotency_key = str(uuid4())

    first = client.post(
        "/api/v1/payments/reservations",
        json=payload,
        headers={"Idempotency-Key": idempotency_key},
    )
    second = client.post(
        "/api/v1/payments/reservations",
        json=payload,
        headers={"Idempotency-Key": idempotency_key},
    )

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED
    assert second.json()["reservation_id"] == first.json()["reservation_id"]


@pytest.mark.unit()
def test_reserve_payment_with_conflicting_idempotency_key_returns_409() -> None:
    client = TestClient(app)

    first_payload = _reserve_payload()
    second_payload = {**first_payload, "amount": "251.00"}
    idempotency_key = str(uuid4())

    first = client.post(
        "/api/v1/payments/reservations",
        json=first_payload,
        headers={"Idempotency-Key": idempotency_key},
    )
    second = client.post(
        "/api/v1/payments/reservations",
        json=second_payload,
        headers={"Idempotency-Key": idempotency_key},
    )

    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["error"]["code"] == "CONFLICT"


@pytest.mark.unit()
def test_confirm_and_refund_payment_endpoints() -> None:
    client = TestClient(app)

    reserve = client.post("/api/v1/payments/reservations", json=_reserve_payload())
    payment_id = reserve.json()["reservation_id"]

    confirm = client.post(f"/api/v1/payments/{payment_id}/confirm")
    assert confirm.status_code == status.HTTP_200_OK
    assert confirm.json()["status"] == "completed"

    refund = client.post(f"/api/v1/payments/{payment_id}/refund")
    assert refund.status_code == status.HTTP_200_OK
    assert refund.json()["status"] == "refunded"


@pytest.mark.unit()
def test_payment_history_endpoint_supports_user_filter() -> None:
    client = TestClient(app)

    user_id = str(uuid4())
    first_payload = _reserve_payload()
    first_payload["user_id"] = user_id
    second_payload = _reserve_payload()

    first = client.post("/api/v1/payments/reservations", json=first_payload)
    client.post("/api/v1/payments/reservations", json=second_payload)

    response = client.get("/api/v1/payments/history", params={"user_id": user_id})

    assert first.status_code == status.HTTP_201_CREATED
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["payment_id"] == first.json()["reservation_id"]


@pytest.mark.unit()
def test_release_payment_returns_404_for_unknown_reservation() -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/payments/reservations/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "NOT_FOUND"
