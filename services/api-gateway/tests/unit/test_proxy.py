"""Unit tests for proxy error handling."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest


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
