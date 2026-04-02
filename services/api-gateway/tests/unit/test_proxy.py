"""Unit tests for proxy error handling."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from shared.common.jwt import create_access_token

from src.config import settings


def _build_access_token() -> str:
    return create_access_token(
        subject="test-user-id",
        secret_key=settings.jwt_secret_key,
        extra_claims={"role": "customer", "email": "test@example.com"},
    )


@pytest.mark.unit
def test_proxy_user_service_timeout(client_with_mocks):
    """Timeouts should map to 504 responses."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 504
        data = response.json()
        assert "timeout" in data["error"]["message"].lower()


@pytest.mark.unit
def test_proxy_user_service_unavailable(client_with_mocks):
    """Connection errors should map to 502 responses."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 502
        data = response.json()
        assert "connect" in data["error"]["message"].lower()


@pytest.mark.unit
def test_proxy_payment_history_requires_jwt(client_with_mocks):
    response = client_with_mocks.get("/api/v1/payments/history")

    assert response.status_code in {401, 403}


@pytest.mark.unit
def test_proxy_payment_history_success(client_with_mocks):
    token = _build_access_token()

    def request_handler(method, url, **kwargs):
        assert method == "GET"
        assert str(url).endswith("/api/v1/payments/history")
        assert kwargs["headers"]["X-User-ID"] == "test-user-id"
        return httpx.Response(status_code=200, json={"items": [], "total": 0})

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=request_handler)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 0
