"""Unit tests for notification service entrypoint."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import create_app


@pytest.mark.unit()
def test_health_endpoint_is_liveness_only() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "dependencies" not in data


@pytest.mark.unit()
def test_ready_endpoint_reports_ready_when_kafka_disabled() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["dependencies"]["kafka_consumer"] == "disabled"


@pytest.mark.unit()
def test_ready_endpoint_returns_503_when_consumer_not_ready() -> None:
    app = create_app()
    consumer = AsyncMock()
    consumer.is_ready = MagicMock(return_value=False)

    with (
        patch("src.main.settings.kafka_enabled", True),
        patch("src.main.get_notification_event_consumer", return_value=consumer),
        patch("src.main.init_event_publisher", new=AsyncMock()),
        patch("src.main.shutdown_event_publisher", new=AsyncMock()),
        patch("src.main.is_event_publisher_ready", return_value=True),
        TestClient(app) as client,
    ):
        response = client.get("/ready")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["dependencies"]["kafka_consumer"] == "unhealthy"
