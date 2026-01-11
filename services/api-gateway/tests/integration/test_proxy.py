"""Integration tests for proxy functionality."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.mark.integration
class TestProxyToUserService:
    """Test proxying requests to User Service."""

    @pytest.fixture
    def mock_httpx_client(self, mock_user_service):
        """Mock httpx.AsyncClient for User Service calls."""
        client_mock = AsyncMock()

        async def mock_request(method, url, **kwargs):
            """Mock HTTP requests to User Service."""
            response_mock = AsyncMock()
            body = kwargs.get("content") or b""
            try:
                json_data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                json_data = {}

            # Determine response based on URL and request data
            if "login" in url:
                # Check if credentials are valid (simple mock logic)
                if json_data.get("email") == "invalid@example.com":
                    response_payload = mock_user_service["login_invalid"]["json"]
                    response_mock.status_code = mock_user_service["login_invalid"]["status_code"]
                else:
                    response_payload = mock_user_service["login_success"]["json"]
                    response_mock.status_code = mock_user_service["login_success"]["status_code"]
            elif "refresh" in url:
                response_payload = mock_user_service["refresh_success"]["json"]
                response_mock.status_code = mock_user_service["refresh_success"]["status_code"]
            elif "users/me" in url:
                response_payload = mock_user_service["user_profile"]["json"]
                response_mock.status_code = mock_user_service["user_profile"]["status_code"]
            else:
                response_payload = {"detail": "Not found"}
                response_mock.status_code = 404

            response_mock.json = AsyncMock(return_value=response_payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(response_payload).encode()
            return response_mock

        client_mock.request = mock_request
        client_mock.__aenter__ = AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = AsyncMock(return_value=None)

        return client_mock

    def test_proxy_login_success(self, client_with_mocks, mock_httpx_client):
        """Test successful login proxying."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            response = client_with_mocks.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    def test_proxy_login_invalid_credentials(self, client_with_mocks, mock_httpx_client):
        """Test login with invalid credentials."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            response = client_with_mocks.post(
                "/api/v1/auth/login",
                json={"email": "invalid@example.com", "password": "wrongpassword"},
            )

            assert response.status_code == 401
            data = response.json()
            assert "detail" in data

    def test_proxy_refresh_token(self, client_with_mocks, mock_httpx_client):
        """Test token refresh proxying."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            response = client_with_mocks.post(
                "/api/v1/auth/refresh", json={"refresh_token": "test_refresh_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    def test_proxy_preserves_headers(self, client_with_mocks, mock_httpx_client):
        """Test that proxy preserves request headers."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            response = client_with_mocks.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password123"},
                headers={"X-Request-ID": "test-request-id", "User-Agent": "Test Client"},
            )

            assert response.status_code == 200

    def test_proxy_user_service_timeout(self, client_with_mocks):
        """Test handling of User Service timeout."""
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

    def test_proxy_user_service_unavailable(self, client_with_mocks):
        """Test handling when User Service is unavailable."""
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
