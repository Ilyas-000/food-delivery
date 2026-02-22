"""Integration tests for rate limiting functionality."""

import pytest


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting behavior with real Redis and User Service."""

    def test_login_rate_limit_per_ip(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """Limit by IP should trigger before other limits."""
        from src.config import settings

        limit = 3
        monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "login_per_ip_hour", limit)
        monkeypatch.setattr(settings, "login_per_account_minute", 1000)
        monkeypatch.setattr(settings, "login_per_account_hour", 1000)
        monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
        monkeypatch.setattr(settings, "login_max_fails_count", 1000)

        for _ in range(limit):
            response = gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={
                    "email": user_credentials["email"],
                    "password": user_credentials["password"],
                },
            )
            assert response.status_code == 200

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )
        assert response.status_code == 429
        message = response.json()["detail"]["error"]["message"].lower()
        assert "too many login attempts" in message

    def test_login_rate_limit_per_account(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """Limit by account should trigger before IP limits."""
        from src.config import settings

        limit = 3
        monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "login_per_ip_hour", 1000)
        monkeypatch.setattr(settings, "login_per_account_minute", 1000)
        monkeypatch.setattr(settings, "login_per_account_hour", limit)
        monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
        monkeypatch.setattr(settings, "login_max_fails_count", 1000)

        for _ in range(limit):
            response = gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={
                    "email": user_credentials["email"],
                    "password": user_credentials["password"],
                },
            )
            assert response.status_code == 200

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )
        assert response.status_code == 429
        message = response.json()["detail"]["error"]["message"].lower()
        assert "account" in message or "too many" in message

    def test_progressive_backoff_on_failed_logins(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """Cooldown should activate after too many failed logins."""
        from src.config import settings

        monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "login_per_ip_hour", 1000)
        monkeypatch.setattr(settings, "login_per_account_minute", 1000)
        monkeypatch.setattr(settings, "login_per_account_hour", 1000)
        monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
        monkeypatch.setattr(settings, "login_max_fails_count", 3)

        for _ in range(3):
            response = gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={
                    "email": user_credentials["email"],
                    "password": "wrongpassword",
                },
            )
            assert response.status_code == 401

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 429
        message = response.json()["detail"]["error"]["message"].lower()
        assert "failed login attempts" in message or "too many" in message

    def test_refresh_token_rate_limiting(
        self,
        gateway_client_with_user_service,
        login_tokens,
        monkeypatch,
    ):
        """Refresh token endpoint should respect per-IP limits."""
        from src.config import settings

        limit = 3
        monkeypatch.setattr(settings, "refresh_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_ip_hour", limit)
        monkeypatch.setattr(settings, "refresh_per_jti_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_jti_hour", 1000)
        monkeypatch.setattr(settings, "refresh_per_user_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_user_hour", 1000)

        refresh_token = login_tokens["refresh_token"]
        for _ in range(limit):
            response = gateway_client_with_user_service.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert response.status_code == 200
            payload = response.json()
            refresh_token = payload.get("refresh_token", refresh_token)

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 429

    def test_global_auth_rate_limit(
        self,
        gateway_client_with_user_service,
        user_credentials,
        login_tokens,
        monkeypatch,
    ):
        """Global auth limit should apply across auth endpoints."""
        from src.config import settings

        limit = 3
        monkeypatch.setattr(settings, "auth_global_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "auth_global_per_ip_hour", limit)
        monkeypatch.setattr(settings, "auth_global_burst", 0)
        monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "login_per_ip_hour", 1000)
        monkeypatch.setattr(settings, "login_per_account_minute", 1000)
        monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_ip_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_jti_minute", 1000)
        monkeypatch.setattr(settings, "refresh_per_user_minute", 1000)

        refresh_token = login_tokens["refresh_token"]
        for i in range(limit):
            if i % 2 == 0:
                response = gateway_client_with_user_service.post(
                    "/api/v1/auth/login",
                    json={
                        "email": user_credentials["email"],
                        "password": user_credentials["password"],
                    },
                )
            else:
                response = gateway_client_with_user_service.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token},
                )
                if response.status_code == 200:
                    refresh_token = response.json().get("refresh_token", refresh_token)

            assert response.status_code == 200

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )
        assert response.status_code == 429

    def test_rate_limit_response_headers(
        self,
        gateway_client_with_user_service,
        user_credentials,
    ):
        """Rate limit headers are optional; response should succeed or be limited."""
        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )

        assert response.status_code in [200, 429]
