"""Integration tests for health check endpoints."""


def test_health_check(gateway_client):
    """Test basic health check endpoint."""
    response = gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"
    assert "version" in data


def test_readiness_check_all_healthy(gateway_client_with_user_service):
    """Test readiness check when all dependencies are healthy."""
    response = gateway_client_with_user_service.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["dependencies"]["redis"] == "healthy"
    assert data["dependencies"]["user_service"] == "healthy"
