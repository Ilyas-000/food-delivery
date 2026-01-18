"""Integration tests for Circuit Breaker functionality."""

import time

import pytest


def _disable_rate_limits(monkeypatch, settings) -> None:
    monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
    monkeypatch.setattr(settings, "login_per_ip_hour", 1000)
    monkeypatch.setattr(settings, "login_per_account_minute", 1000)
    monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
    monkeypatch.setattr(settings, "login_max_fails_count", 1000)
    monkeypatch.setattr(settings, "login_max_fails_window", 10_000)
    monkeypatch.setattr(settings, "auth_global_per_ip_minute", 1000)
    monkeypatch.setattr(settings, "auth_global_burst", 1000)


@pytest.mark.integration
class TestCircuitBreaker:
    """Test Circuit Breaker middleware with real gateway wiring."""

    def test_circuit_breaker_opens_after_failures(self, gateway_client, monkeypatch):
        """Circuit breaker should open after threshold failures."""
        from src.config import settings

        monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
        _disable_rate_limits(monkeypatch, settings)

        for _ in range(settings.circuit_breaker_failure_threshold):
            response = gateway_client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password"},
            )
            assert response.status_code == 502

        response = gateway_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"},
        )
        assert response.status_code == 503
        details = response.json()["error"]["details"].lower()
        assert "circuit breaker" in details or "unavailable" in details

    def test_circuit_breaker_half_open_after_timeout(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """Circuit breaker should allow a probe after recovery timeout."""
        from src.config import settings

        original_url = settings.user_service_url
        monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
        _disable_rate_limits(monkeypatch, settings)

        for _ in range(settings.circuit_breaker_failure_threshold):
            gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password"},
            )

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"},
        )
        assert response.status_code == 503

        future_time = time.time() + settings.circuit_breaker_recovery_timeout + 1
        monkeypatch.setattr("src.middleware.circuit_breaker.time.time", lambda: future_time)
        monkeypatch.setattr(settings, "user_service_url", original_url)

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": user_credentials["password"],
            },
        )
        assert response.status_code == 200

    def test_circuit_breaker_closes_after_successful_request(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """Circuit breaker should close after a successful probe."""
        from src.config import settings

        original_url = settings.user_service_url
        monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
        _disable_rate_limits(monkeypatch, settings)

        for _ in range(settings.circuit_breaker_failure_threshold):
            gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password"},
            )

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"},
        )
        assert response.status_code == 503

        future_time = time.time() + settings.circuit_breaker_recovery_timeout + 1
        monkeypatch.setattr("src.middleware.circuit_breaker.time.time", lambda: future_time)
        monkeypatch.setattr(settings, "user_service_url", original_url)

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
        assert response.status_code == 200

    def test_circuit_breaker_counts_only_connection_errors(
        self,
        gateway_client_with_user_service,
        user_credentials,
        monkeypatch,
    ):
        """4xx responses should not open the circuit."""
        from src.config import settings

        _disable_rate_limits(monkeypatch, settings)

        for _ in range(10):
            response = gateway_client_with_user_service.post(
                "/api/v1/auth/login",
                json={
                    "email": user_credentials["email"],
                    "password": "wrong",
                },
            )
            assert response.status_code == 401

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={
                "email": user_credentials["email"],
                "password": "wrong",
            },
        )
        assert response.status_code == 401

    def test_circuit_breaker_different_services(self):
        """Placeholder: multiple services not wired yet."""
        pass
