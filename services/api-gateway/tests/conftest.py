"""Pytest fixtures for API Gateway tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytest_plugins = ["shared.testing.pytest_summary"]

# Set test environment variables before importing app
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("GATEWAY_LOGIN_PER_IP_MINUTE", "10")
os.environ.setdefault("GATEWAY_LOGIN_PER_ACCOUNT_MINUTE", "5")
os.environ.setdefault("GATEWAY_REFRESH_PER_IP_MINUTE", "60")
os.environ.setdefault("GATEWAY_AUTH_GLOBAL_PER_IP_MINUTE", "60")
os.environ.setdefault("GATEWAY_USER_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("GATEWAY_REDIS_HOST", "localhost")
os.environ.setdefault("GATEWAY_REDIS_PORT", "6379")

from src.main import app  # noqa: E402


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.incr = AsyncMock(return_value=1)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.ttl = AsyncMock(return_value=-2)  # -2 means key doesn't exist
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.close = AsyncMock()

    # Mock pipeline
    pipeline_mock = MagicMock()
    pipeline_mock.incr = MagicMock(return_value=None)
    pipeline_mock.expire = MagicMock(return_value=None)
    pipeline_mock.execute = AsyncMock(return_value=[1, True])
    redis_mock.pipeline = MagicMock(return_value=pipeline_mock)

    return redis_mock


@pytest.fixture
def mock_user_service():
    """Mock responses from User Service."""
    return {
        "login_success": {
            "status_code": 200,
            "json": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "bearer",
            },
        },
        "login_invalid": {"status_code": 401, "json": {"detail": "Invalid credentials"}},
        "refresh_success": {
            "status_code": 200,
            "json": {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "token_type": "bearer",
            },
        },
        "refresh_invalid": {"status_code": 401, "json": {"detail": "Invalid refresh token"}},
        "user_profile": {
            "status_code": 200,
            "json": {
                "id": "test-user-id",
                "email": "test@example.com",
                "full_name": "Test User",
                "role": "customer",
            },
        },
    }


@pytest.fixture
def client_with_mocks(mock_redis):
    """Test client with mocked Redis and disabled circuit breaker for easier testing."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

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

    with patch("src.deps.redis._redis_client", mock_redis):
        with patch("src.deps.redis.get_redis", return_value=mock_redis):
            yield TestClient(test_app)


@pytest.fixture
def client_with_circuit_breaker(mock_redis):
    """Test client with mocked Redis and circuit breaker enabled."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from src.config import settings
    from src.middleware.circuit_breaker import CircuitBreakerMiddleware
    from src.middleware.logging import RequestLoggingMiddleware
    from src.routes import health, proxy

    test_app = FastAPI(title="Test API Gateway")

    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(
        CircuitBreakerMiddleware,
        failure_threshold=settings.circuit_breaker_failure_threshold,
        recovery_timeout=settings.circuit_breaker_recovery_timeout,
    )
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    test_app.include_router(health.router, tags=["Health"])
    test_app.include_router(proxy.router, tags=["Proxy"])

    with patch("src.deps.redis._redis_client", mock_redis):
        with patch("src.deps.redis.get_redis", return_value=mock_redis):
            yield TestClient(test_app)


@pytest.fixture
def client():
    """Test client for API Gateway."""
    return TestClient(app)
