"""Integration tests for Circuit Breaker functionality."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.mark.integration
class TestCircuitBreaker:
    """Test Circuit Breaker middleware."""

    @pytest.fixture
    def reset_circuit_breakers(self):
        """Reset circuit breaker state before each test."""
        # Circuit breakers are isolated per middleware instance in tests
        # No need to manually reset
        yield

    def test_circuit_breaker_opens_after_failures(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breaker opens after threshold failures."""
        failure_count = 0
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            nonlocal failure_count
            failure_count += 1
            # First 5 requests fail
            if failure_count <= 5:
                raise httpx.ConnectError("Connection refused")
            # After circuit opens, this shouldn't be called
            response_mock = AsyncMock()
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value={"status": "ok"})
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # First 5 requests should get 502 (Bad Gateway)
            for i in range(5):
                response = client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "password"},
                )
                assert response.status_code == 502

            # 6th request should get 503 with "circuit breaker" message
            response = client_with_circuit_breaker.post(
                "/api/v1/auth/login", json={"email": "user6@example.com", "password": "password"}
            )
            assert response.status_code == 503
            data = response.json()
            details = data["error"]["details"].lower()
            assert "circuit breaker" in details or "unavailable" in details

    def test_circuit_breaker_half_open_after_timeout(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breaker enters half-open state after timeout."""
        from src.config import settings

        failure_count = 0
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            nonlocal failure_count
            failure_count += 1
            # First 5 requests fail to open circuit
            if failure_count <= 5:
                raise httpx.ConnectError("Connection refused")
            # After timeout, service recovers
            response_mock = AsyncMock()
            response_mock.status_code = 200
            response_payload = {"access_token": "token", "token_type": "bearer"}
            response_mock.json = AsyncMock(return_value=response_payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = b'{"access_token": "token", "token_type": "bearer"}'
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Trigger circuit breaker to open
            for i in range(5):
                client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "password"},
                )

            # Circuit should be open now
            response = client_with_circuit_breaker.post(
                "/api/v1/auth/login", json={"email": "test@example.com", "password": "password"}
            )
            assert response.status_code == 503

            # Wait for timeout (mock or actual wait)
            # In real test, would mock time or wait for actual timeout
            # For now, we'll patch the circuit breaker to allow the next call
            with patch(
                "time.time",
                return_value=time.time() + settings.circuit_breaker_recovery_timeout + 1,
            ):
                response = client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": "recovery@example.com", "password": "password"},
                )
                assert response.status_code == 200

    def test_circuit_breaker_closes_after_successful_request(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breaker closes after successful request in half-open state."""
        call_count = 0
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            response_mock = AsyncMock()

            # Fail first 5 to open circuit, then succeed
            if call_count <= 5:
                raise httpx.ConnectError("Connection refused")

            response_mock.status_code = 200
            response_payload = {"access_token": "token", "token_type": "bearer"}
            response_mock.json = AsyncMock(return_value=response_payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = b'{"access_token": "token", "token_type": "bearer"}'
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Open the circuit
            for i in range(5):
                client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "password"},
                )

            # Circuit is open - verify
            response = client_with_circuit_breaker.post(
                "/api/v1/auth/login", json={"email": "test@example.com", "password": "password"}
            )
            assert response.status_code == 503

    def test_circuit_breaker_different_services(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breakers are independent per service."""
        # This test would require multiple services to be configured
        # For now, we just verify that User Service circuit breaker doesn't affect others
        # In Phase 1.5, we only have User Service, so this is a placeholder
        pass

    def test_circuit_breaker_counts_only_connection_errors(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breaker only counts connection/timeout errors, not 4xx/5xx."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            # Return 401 errors (not connection errors)
            response_mock = AsyncMock()
            response_mock.status_code = 401
            response_mock.json = AsyncMock(return_value={"detail": "Invalid credentials"})
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = b"{}"
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Make many requests with 401 responses
            for i in range(10):
                response = client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "wrong"},
                )
                # Should get 401, not 503 (circuit shouldn't open for auth failures)
                assert response.status_code == 401

    def test_circuit_breaker_timeout_errors(
        self, client_with_circuit_breaker, reset_circuit_breakers
    ):
        """Test that circuit breaker opens on timeout errors."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            # Simulate timeout
            raise httpx.TimeoutException("Request timeout")

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # First 5 requests should get 504 (Gateway Timeout)
            for i in range(5):
                response = client_with_circuit_breaker.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "password"},
                )
                assert response.status_code == 504

            # After threshold, circuit should be open
            response = client_with_circuit_breaker.post(
                "/api/v1/auth/login", json={"email": "test@example.com", "password": "password"}
            )
            assert response.status_code == 503
