"""Integration tests for health check endpoints."""

import pytest


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"
    assert "version" in data


@pytest.mark.skip(reason="Requires Redis and User Service running")
def test_readiness_check_all_healthy(client):
    """Test readiness check when all dependencies are healthy."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["dependencies"]["redis"] == "healthy"
    assert data["dependencies"]["user_service"] == "healthy"
