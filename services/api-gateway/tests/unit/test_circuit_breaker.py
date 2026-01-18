"""Unit tests for circuit breaker edge cases."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.mark.unit
def test_circuit_breaker_opens_on_timeouts(client_with_circuit_breaker):
    """Timeouts should open the circuit after threshold."""
    mock_client = AsyncMock()

    async def mock_request(method, url, **kwargs):
        raise httpx.TimeoutException("Request timeout")

    mock_client.request = mock_request
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        for _ in range(5):
            response = client_with_circuit_breaker.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "password"},
            )
            assert response.status_code == 504

        response = client_with_circuit_breaker.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password"},
        )
        assert response.status_code == 503
