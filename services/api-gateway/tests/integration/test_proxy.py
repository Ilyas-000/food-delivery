"""Integration tests for proxy functionality."""

import pytest

from src.config import settings


@pytest.mark.integration
class TestProxyToUserService:
    """Test proxying requests to User Service."""

    def test_proxy_login_success(self, gateway_client_with_user_service, user_credentials):
        """Test successful login proxying."""
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_proxy_login_invalid_credentials(
        self,
        gateway_client_with_user_service,
        user_credentials,
    ):
        """Test login with invalid credentials."""
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={"email": user_credentials["email"], "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["message"]

    def test_proxy_refresh_token(self, gateway_client_with_user_service, login_tokens):
        """Test token refresh proxying."""
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_tokens["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_proxy_preserves_headers(self, gateway_client_with_user_service, user_credentials):
        """Test that proxy preserves request headers."""
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
            headers={"X-Request-ID": "test-request-id", "User-Agent": "Test Client"},
        )

        assert response.status_code == 200

    def test_proxy_user_service_unavailable(self, gateway_client_with_user_service, monkeypatch):
        """Test handling when User Service is unavailable."""
        monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 502
        data = response.json()
        assert "connect" in data["error"]["message"].lower()
