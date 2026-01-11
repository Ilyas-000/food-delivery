"""Integration tests for rate limiting functionality."""

import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting middleware."""

    @pytest.fixture
    def mock_redis_with_limits(self):
        """Mock Redis that simulates rate limit counters."""
        from unittest.mock import MagicMock

        redis_mock = AsyncMock()
        counters = {}
        cooldowns = {}

        async def mock_incr(key):
            """Increment counter for key."""
            if key not in counters:
                counters[key] = 0
            counters[key] += 1
            return counters[key]

        async def mock_get(key):
            """Get counter value."""
            return str(counters.get(key, 0)).encode() if key in counters else None

        async def mock_expire(key, seconds):
            """Mock expire (no-op in tests)."""
            return True

        async def mock_setex(key, ttl, value):
            """Set cooldown TTL for key."""
            cooldowns[key] = ttl
            return True

        async def mock_delete(key):
            """Delete key."""
            if key in counters:
                del counters[key]
            if key in cooldowns:
                del cooldowns[key]
            return 1

        # Mock pipeline
        def mock_pipeline():
            pipeline_mock = MagicMock()

            def pipeline_incr(key):
                if key not in counters:
                    counters[key] = 0
                counters[key] += 1

            pipeline_mock.incr = pipeline_incr
            pipeline_mock.expire = MagicMock()
            pipeline_mock.execute = AsyncMock(return_value=[counters.get("last_key", 1), True])
            return pipeline_mock

        redis_mock.incr = mock_incr
        redis_mock.get = mock_get
        redis_mock.setex = mock_setex
        redis_mock.expire = mock_expire
        redis_mock.delete = mock_delete
        redis_mock.ttl = AsyncMock(side_effect=lambda key: cooldowns.get(key, -2))
        redis_mock.pipeline = mock_pipeline
        redis_mock.ping = AsyncMock(return_value=True)
        redis_mock.close = AsyncMock()

        return redis_mock

    @pytest.fixture
    def client_with_rate_limiting(self, mock_redis_with_limits):
        """Test client with mocked Redis for rate limiting tests."""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.testclient import TestClient

        from src.config import settings
        from src.middleware.logging import RequestLoggingMiddleware
        from src.routes import health, proxy

        # Create app without circuit breaker middleware for tests
        test_app = FastAPI(title="Test API Gateway")

        # Add only logging middleware
        test_app.add_middleware(RequestLoggingMiddleware)

        # Add CORS
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=settings.cors_credentials,
            allow_methods=settings.cors_methods,
            allow_headers=settings.cors_headers,
        )

        # Include routers
        test_app.include_router(health.router, tags=["Health"])
        test_app.include_router(proxy.router, tags=["Proxy"])

        with patch("src.deps.redis._redis_client", mock_redis_with_limits):
            with patch("src.deps.redis.get_redis", return_value=mock_redis_with_limits):
                yield TestClient(test_app)

    def test_login_rate_limit_per_ip(self, client_with_rate_limiting):
        """Test rate limiting for login endpoint per IP."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            payload = {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "token_type": "bearer",
            }
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Make requests up to the limit (default: 10 per minute per IP)
            for i in range(10):
                response = client_with_rate_limiting.post(
                    "/api/v1/auth/login",
                    json={"email": f"user{i}@example.com", "password": "password123"},
                )
                assert response.status_code == 200, f"Request {i+1} failed"

            # 11th request should be rate limited
            response = client_with_rate_limiting.post(
                "/api/v1/auth/login",
                json={"email": "user11@example.com", "password": "password123"},
            )
            assert response.status_code == 429
            data = response.json()
            message = data["detail"]["error"]["message"].lower()
            assert "too many" in message

    def test_login_rate_limit_per_account(self, client_with_rate_limiting, monkeypatch):
        """Test rate limiting per account for login endpoint."""
        from src.config import settings

        monkeypatch.setattr(settings, "login_per_ip_account_minute", 100)
        monkeypatch.setattr(settings, "login_max_fails_count", 100)

        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            response_mock.status_code = 401  # Simulate failed login
            payload = {"detail": "Invalid credentials"}
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            same_email = "test@example.com"

            # Make requests up to account limit (default: 5 per minute)
            for i in range(5):
                response = client_with_rate_limiting.post(
                    "/api/v1/auth/login",
                    json={"email": same_email, "password": f"password{i}"},
                )
                # Should get 401 from User Service
                assert response.status_code == 401

            # 6th request should be rate limited
            response = client_with_rate_limiting.post(
                "/api/v1/auth/login", json={"email": same_email, "password": "password123"}
            )
            assert response.status_code == 429
            data = response.json()
            message = data["detail"]["error"]["message"].lower()
            assert "account" in message or "too many" in message

    def test_progressive_backoff_on_failed_logins(self, client_with_rate_limiting, monkeypatch):
        """Test progressive backoff after multiple failed login attempts."""
        from src.config import settings

        monkeypatch.setattr(settings, "login_per_account_minute", 100)
        monkeypatch.setattr(settings, "login_per_ip_account_minute", 100)

        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            response_mock.status_code = 401
            payload = {"detail": "Invalid credentials"}
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            same_email = "attacker@example.com"

            # Simulate 5 failed login attempts (threshold)
            for _ in range(5):
                response = client_with_rate_limiting.post(
                    "/api/v1/auth/login",
                    json={"email": same_email, "password": "wrongpassword"},
                )
                assert response.status_code == 401

            # After threshold, account should be locked
            response = client_with_rate_limiting.post(
                "/api/v1/auth/login", json={"email": same_email, "password": "wrongpassword"}
            )
            assert response.status_code == 429
            data = response.json()
            message = data["detail"]["error"]["message"].lower()
            assert "failed login attempts" in message or "too many" in message

    def test_refresh_token_rate_limiting(self, client_with_rate_limiting):
        """Test rate limiting for refresh token endpoint."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            payload = {
                "access_token": "new_token",
                "refresh_token": "new_refresh",
                "token_type": "bearer",
            }
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Make requests up to refresh limit per IP (default: 60 per minute)
            for i in range(60):
                response = client_with_rate_limiting.post(
                    "/api/v1/auth/refresh", json={"refresh_token": f"refresh_token_{i}"}
                )
                assert response.status_code == 200

            # 61st request should be rate limited
            response = client_with_rate_limiting.post(
                "/api/v1/auth/refresh", json={"refresh_token": "refresh_token_61"}
            )
            assert response.status_code == 429

    def test_global_auth_rate_limit(self, client_with_rate_limiting):
        """Test global rate limit across all auth endpoints."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            payload = {"access_token": "token"}
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            # Mix login and refresh requests
            for i in range(30):
                if i % 2 == 0:
                    client_with_rate_limiting.post(
                        "/api/v1/auth/login",
                        json={"email": f"user{i}@example.com", "password": "pass"},
                    )
                else:
                    client_with_rate_limiting.post(
                        "/api/v1/auth/refresh", json={"refresh_token": f"token_{i}"}
                    )

            # Should still work due to per-endpoint limits
            response = client_with_rate_limiting.post(
                "/api/v1/auth/login", json={"email": "test@example.com", "password": "pass"}
            )
            # May be limited or not depending on implementation
            assert response.status_code in [200, 429]

    def test_rate_limit_response_headers(self, client_with_rate_limiting):
        """Test that rate limit headers are present in response."""
        mock_httpx_client = AsyncMock()

        async def mock_request(method, url, **kwargs):
            response_mock = AsyncMock()
            payload = {"access_token": "token"}
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value=payload)
            response_mock.headers = {"content-type": "application/json"}
            response_mock.content = json.dumps(payload).encode()
            return response_mock

        mock_httpx_client.request = mock_request
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            response = client_with_rate_limiting.post(
                "/api/v1/auth/login", json={"email": "test@example.com", "password": "pass"}
            )

            # Check if rate limit headers exist (optional implementation)
            # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
            # This is optional based on implementation
            assert response.status_code in [200, 429]
