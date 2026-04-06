"""Pytest fixtures for API Gateway tests."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
import redis
from fastapi.testclient import TestClient

pytest_plugins = ["shared.testing.pytest_summary"]

# Set test environment variables before importing app
os.environ.setdefault("GATEWAY_JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("GATEWAY_LOGIN_PER_IP_MINUTE", "10")
os.environ.setdefault("GATEWAY_LOGIN_PER_ACCOUNT_MINUTE", "5")
os.environ.setdefault("GATEWAY_REFRESH_PER_IP_MINUTE", "60")
os.environ.setdefault("GATEWAY_AUTH_GLOBAL_PER_IP_MINUTE", "60")
os.environ.setdefault("GATEWAY_USER_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("GATEWAY_ORDER_SERVICE_URL", "http://localhost:8003")
os.environ.setdefault("GATEWAY_PAYMENT_SERVICE_URL", "http://localhost:8004")
os.environ.setdefault("GATEWAY_DELIVERY_SERVICE_URL", "http://localhost:8005")
os.environ.setdefault("GATEWAY_ANALYTICS_SERVICE_URL", "http://localhost:8007")
os.environ.setdefault("GATEWAY_REDIS_HOST", "localhost")
os.environ.setdefault("GATEWAY_REDIS_PORT", "6379")
os.environ.setdefault("GATEWAY_REDIS_DB", "15")

from src.config import settings  # noqa: E402
from src.main import create_app  # noqa: E402

_TEST_JWT_SECRET = "test-secret-key-for-testing-only"


def _read_env_value(key: str) -> str | None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() != key:
            continue
        value = value.strip().strip("'").strip('"')
        return value or None
    return None


def _resolve_user_service_secret() -> str | None:
    env_secret = os.getenv("USER_SERVICE_JWT_SECRET_KEY")
    if env_secret and env_secret != _TEST_JWT_SECRET:
        return env_secret

    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and env_secret != _TEST_JWT_SECRET:
        return env_secret

    file_secret = _read_env_value("USER_SERVICE_JWT_SECRET_KEY") or _read_env_value(
        "JWT_SECRET_KEY"
    )
    return file_secret


def _align_gateway_secret_with_user_service() -> None:
    secret = _resolve_user_service_secret()
    if secret:
        settings.jwt_secret_key = secret


def _get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=True,
    )


def _is_redis_ready() -> bool:
    try:
        client = _get_redis_client()
        client.ping()
        return True
    except Exception:
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def _flush_redis() -> None:
    client = _get_redis_client()
    try:
        client.flushdb()
    finally:
        client.close()


def _is_user_service_ready() -> bool:
    try:
        response = httpx.get(f"{settings.user_service_url}/health", timeout=2.0, trust_env=False)
    except httpx.RequestError:
        return False
    return response.status_code == 200


def _is_order_service_ready() -> bool:
    try:
        response = httpx.get(f"{settings.order_service_url}/health", timeout=2.0, trust_env=False)
    except httpx.RequestError:
        return False
    return response.status_code == 200


def _is_analytics_service_ready() -> bool:
    try:
        response = httpx.get(
            f"{settings.analytics_service_url}/health",
            timeout=2.0,
            trust_env=False,
        )
    except httpx.RequestError:
        return False
    return response.status_code == 200


@pytest.fixture
def gateway_client() -> TestClient:
    """Gateway client backed by real Redis (integration)."""
    if not _is_redis_ready():
        pytest.skip("Redis is not available for integration tests")
    _align_gateway_secret_with_user_service()
    _flush_redis()
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def gateway_client_with_user_service() -> TestClient:
    """Gateway client with real Redis + User Service (integration)."""
    if not _is_redis_ready():
        pytest.skip("Redis is not available for integration tests")
    _align_gateway_secret_with_user_service()
    if not _is_user_service_ready():
        pytest.skip(f"User Service not available at {settings.user_service_url}")
    if not _is_order_service_ready():
        pytest.skip(f"Order Service not available at {settings.order_service_url}")
    _flush_redis()
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def gateway_client_with_analytics_service() -> TestClient:
    """Gateway client with real Redis + Analytics Service (integration)."""
    if not _is_redis_ready():
        pytest.skip("Redis is not available for integration tests")
    if not _is_analytics_service_ready():
        pytest.skip(f"Analytics Service not available at {settings.analytics_service_url}")
    _align_gateway_secret_with_user_service()
    _flush_redis()
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def user_credentials(gateway_client_with_user_service) -> dict[str, str]:
    """Create a real user via the gateway and return credentials."""
    email = f"test-{uuid4()}@example.com"
    password = "SecurePass123!"
    response = gateway_client_with_user_service.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    _flush_redis()
    return {"email": email, "password": password}


@pytest.fixture
def login_tokens(
    gateway_client_with_user_service,
    user_credentials,
) -> dict[str, str]:
    """Login with a real user and return access/refresh tokens."""
    response = gateway_client_with_user_service.post(
        "/api/v1/auth/login",
        json={
            "email": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    _flush_redis()
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
    }


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
        "login_invalid": {
            "status_code": 401,
            "json": {"error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}},
        },
        "refresh_success": {
            "status_code": 200,
            "json": {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "token_type": "bearer",
            },
        },
        "refresh_invalid": {
            "status_code": 401,
            "json": {"error": {"code": "UNAUTHORIZED", "message": "Invalid refresh token"}},
        },
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

    _align_gateway_secret_with_user_service()

    with patch("src.dependencies.redis_client._redis_client", mock_redis):
        with patch("src.dependencies.redis_client.get_redis", return_value=mock_redis):
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

    with patch("src.dependencies.redis_client._redis_client", mock_redis):
        with patch("src.dependencies.redis_client.get_redis", return_value=mock_redis):
            yield TestClient(test_app)


@pytest.fixture
def client():
    """Test client for API Gateway."""
    return TestClient(create_app())
