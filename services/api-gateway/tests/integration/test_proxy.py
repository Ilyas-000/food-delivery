"""Integration tests for proxy functionality."""

import pytest
from shared.common.jwt import create_access_token

from src.config import settings


def _build_access_token() -> str:
    return create_access_token(
        subject="analytics-user-id",
        secret_key=settings.jwt_secret_key,
        extra_claims={"role": "admin", "email": "analytics@example.com"},
    )


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


@pytest.mark.integration
class TestProxyToAnalyticsService:
    """Test proxying analytics requests through gateway."""

    def test_proxy_analytics_overview_success(self, gateway_client_with_analytics_service):
        token = _build_access_token()

        response = gateway_client_with_analytics_service.get(
            "/api/v1/analytics/overview",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data
        assert "gross_revenue" in data

    def test_proxy_analytics_events_success(self, gateway_client_with_analytics_service):
        token = _build_access_token()

        response = gateway_client_with_analytics_service.get(
            "/api/v1/analytics/events",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.integration
class TestProxyToReviewService:
    """Test proxying review requests through gateway."""

    def test_proxy_review_rating_success(self, gateway_client_with_review_service):
        restaurant_id = "22222222-2222-2222-2222-222222222222"

        response = gateway_client_with_review_service.get(
            f"/api/v1/reviews/restaurants/{restaurant_id}/rating"
        )

        assert response.status_code == 200
        data = response.json()
        assert "average_rating" in data
        assert "reviews_count" in data

    def test_proxy_courier_review_rating_success(self, gateway_client_with_review_service):
        courier_id = "44444444-4444-4444-4444-444444444444"

        response = gateway_client_with_review_service.get(
            f"/api/v1/reviews/couriers/{courier_id}/rating"
        )

        assert response.status_code == 200
        data = response.json()
        assert "average_rating" in data
        assert "reviews_count" in data
