"""Unit tests for analytics service entrypoint."""

from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.main import create_app


@pytest.mark.unit()
def test_health_endpoint_reports_memory_backend_state() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dependencies"]["storage"] == "memory"


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_lifespan_starts_repository_and_consumer_when_kafka_enabled() -> None:
    app = create_app()
    repository = AsyncMock()
    repository.is_ready.return_value = True
    consumer = AsyncMock()
    consumer.is_ready.return_value = True

    with (
        patch("src.main.settings.kafka_enabled", True),
        patch("src.main.get_analytics_repository_instance", return_value=repository),
        patch("src.main.get_analytics_event_consumer", return_value=consumer),
    ):
        async with app.router.lifespan_context(app):
            repository.start.assert_awaited_once()
            consumer.start.assert_awaited_once()

    consumer.stop.assert_awaited_once()
    repository.stop.assert_awaited_once()
