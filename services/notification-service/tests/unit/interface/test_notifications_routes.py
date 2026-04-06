"""Unit tests for notification routes."""

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import app


@pytest.mark.unit()
def test_send_email_notification_endpoint() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/notifications/email",
        json={
            "recipient": "user-1@notifications.local",
            "template_name": "order_created_email",
            "template_context": {"order_id": "order-1"},
            "aggregate_id": "order-1",
            "event_type": "manual.email.requested",
            "user_id": "user-1",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["notification_type"] == "email"
    assert data["status"] == "sent"
    assert data["provider_message_id"] == "email-1"


@pytest.mark.unit()
def test_list_notifications_endpoint_returns_created_items() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/notifications/email",
        json={
            "recipient": "user-1@notifications.local",
            "template_name": "order_created_email",
            "template_context": {"order_id": "order-1"},
            "aggregate_id": "order-1",
            "event_type": "manual.email.requested",
        },
    )

    response = client.get("/api/v1/notifications")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["template_name"] == "order_created_email"
