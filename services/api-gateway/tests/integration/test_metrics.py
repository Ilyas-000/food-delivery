"""Integration tests for gateway observability metrics."""

import pytest
from prometheus_client.parser import text_string_to_metric_families


def _disable_login_limits(monkeypatch, settings) -> None:
    monkeypatch.setattr(settings, "login_per_ip_minute", 1000)
    monkeypatch.setattr(settings, "login_per_ip_hour", 1000)
    monkeypatch.setattr(settings, "login_per_account_minute", 1000)
    monkeypatch.setattr(settings, "login_per_account_hour", 1000)
    monkeypatch.setattr(settings, "login_per_ip_account_minute", 1000)
    monkeypatch.setattr(settings, "login_max_fails_count", 1000)


def _sample_value(payload: str, metric_name: str, labels: dict[str, str]) -> float | None:
    for family in text_string_to_metric_families(payload):
        for sample in family.samples:
            if sample.name != metric_name:
                continue
            sample_labels = {key: str(value) for key, value in sample.labels.items()}
            if all(sample_labels.get(key) == value for key, value in labels.items()):
                return float(sample.value)
    return None


pytestmark = pytest.mark.integration


def test_metrics_endpoint_exposes_http_metrics(gateway_client) -> None:
    health_response = gateway_client.get("/health", headers={"X-Correlation-ID": "gw-corr"})
    metrics_response = gateway_client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert metrics_response.headers["content-type"].startswith("text/plain")
    assert health_response.headers["X-Correlation-ID"] == "gw-corr"
    assert health_response.headers["X-Request-ID"]
    assert (
        _sample_value(
            metrics_response.text,
            "food_delivery_http_requests_total",
            {
                "service": "api-gateway",
                "method": "GET",
                "path": "/health",
                "status_code": "200",
            },
        )
        == 1.0
    )


def test_circuit_breaker_metrics_capture_failures_and_rejections(
    gateway_client,
    monkeypatch,
) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "user_service_url", "http://127.0.0.1:1")
    _disable_login_limits(monkeypatch, settings)
    monkeypatch.setattr(settings, "auth_global_per_ip_minute", 1000)
    monkeypatch.setattr(settings, "auth_global_per_ip_hour", 1000)
    monkeypatch.setattr(settings, "auth_global_burst", 1000)

    for _ in range(settings.circuit_breaker_failure_threshold):
        response = gateway_client.post(
            "/api/v1/auth/login",
            json={"email": "metrics@example.com", "password": "password"},
        )
        assert response.status_code == 502

    rejected_response = gateway_client.post(
        "/api/v1/auth/login",
        json={"email": "metrics@example.com", "password": "password"},
    )
    metrics_response = gateway_client.get("/metrics")

    assert rejected_response.status_code == 503
    assert _sample_value(
        metrics_response.text,
        "food_delivery_gateway_circuit_breaker_failures_total",
        {"downstream_service": "user-service"},
    ) == float(settings.circuit_breaker_failure_threshold)
    assert (
        _sample_value(
            metrics_response.text,
            "food_delivery_gateway_circuit_breaker_rejections_total",
            {"downstream_service": "user-service"},
        )
        == 1.0
    )
    assert (
        _sample_value(
            metrics_response.text,
            "food_delivery_gateway_circuit_breaker_state",
            {"downstream_service": "user-service", "state": "open"},
        )
        == 1.0
    )


def test_rate_limit_metrics_capture_allowed_and_rejected_checks(
    gateway_client_with_user_service,
    user_credentials,
    monkeypatch,
) -> None:
    from src.config import settings

    _disable_login_limits(monkeypatch, settings)
    monkeypatch.setattr(settings, "auth_global_per_ip_minute", 1000)
    monkeypatch.setattr(settings, "auth_global_per_ip_hour", 1)
    monkeypatch.setattr(settings, "auth_global_burst", 0)

    first = gateway_client_with_user_service.post(
        "/api/v1/auth/login",
        json={
            "email": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    second = gateway_client_with_user_service.post(
        "/api/v1/auth/login",
        json={
            "email": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    metrics_response = gateway_client_with_user_service.get("/metrics")

    assert first.status_code == 200
    assert second.status_code == 429
    assert (
        _sample_value(
            metrics_response.text,
            "food_delivery_gateway_rate_limit_decisions_total",
            {"scope": "auth_global_hour", "result": "allowed"},
        )
        >= 1.0
    )
    assert (
        _sample_value(
            metrics_response.text,
            "food_delivery_gateway_rate_limit_decisions_total",
            {"scope": "auth_global_hour", "result": "rejected"},
        )
        >= 1.0
    )
