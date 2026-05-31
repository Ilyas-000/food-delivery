"""Unit tests for payment metrics route."""

from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families
import pytest
from starlette import status

from src.main import create_app

EXPECTED_SINGLE_OBSERVATION = 1.0


def _find_sample_value(
    payload: str,
    metric_name: str,
    labels: dict[str, str],
) -> float | None:
    for family in text_string_to_metric_families(payload):
        for sample in family.samples:
            if sample.name != metric_name:
                continue
            sample_labels = {key: str(value) for key, value in sample.labels.items()}
            if all(sample_labels.get(key) == value for key, value in labels.items()):
                return float(sample.value)
    return None


@pytest.mark.unit()
def test_metrics_endpoint_exposes_http_metrics() -> None:
    client = TestClient(create_app())

    health_response = client.get("/health", headers={"X-Correlation-ID": "corr-123"})
    reserve_response = client.post(
        "/api/v1/payments/reservations",
        json={
            "order_id": "11111111-1111-1111-1111-111111111111",
            "user_id": "22222222-2222-2222-2222-222222222222",
            "amount": "120.00",
            "currency": "RUB",
        },
    )
    metrics_response = client.get("/metrics")

    assert health_response.status_code == status.HTTP_200_OK
    assert reserve_response.status_code == status.HTTP_201_CREATED
    assert metrics_response.status_code == status.HTTP_200_OK
    assert metrics_response.headers["content-type"].startswith("text/plain")
    assert health_response.headers["X-Correlation-ID"] == "corr-123"
    assert health_response.headers["X-Request-ID"]
    assert (
        _find_sample_value(
            metrics_response.text,
            "food_delivery_http_requests_total",
            {
                "service": "payment-service",
                "method": "GET",
                "path": "/health",
                "status_code": "200",
            },
        )
        == EXPECTED_SINGLE_OBSERVATION
    )
    assert (
        _find_sample_value(
            metrics_response.text,
            "food_delivery_payment_reservations_total",
            {"result": "success"},
        )
        == EXPECTED_SINGLE_OBSERVATION
    )
    assert (
        _find_sample_value(
            metrics_response.text,
            "food_delivery_http_request_duration_seconds_count",
            {
                "service": "payment-service",
                "method": "GET",
                "path": "/health",
            },
        )
        == EXPECTED_SINGLE_OBSERVATION
    )
