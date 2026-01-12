import os
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from src.config import settings

_DEFAULT_JWT_SECRET = "your-super-secret-key-change-in-production"
_TEST_JWT_SECRET = "test-secret-key-for-testing-only"


def _is_user_service_ready(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/health", timeout=2.0)
    except httpx.RequestError:
        return False
    return response.status_code == 200


def _read_env_value(key: str) -> str | None:
    env_path = Path(__file__).resolve().parents[4] / ".env"
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


def _resolve_user_service_secret() -> str:
    env_secret = os.getenv("USER_SERVICE_JWT_SECRET_KEY")
    if env_secret:
        return env_secret

    env_secret = os.getenv("JWT_SECRET_KEY")
    if env_secret and env_secret != _TEST_JWT_SECRET:
        return env_secret

    env_secret = os.getenv("GATEWAY_JWT_SECRET_KEY")
    if env_secret and env_secret != _TEST_JWT_SECRET:
        return env_secret

    file_secret = _read_env_value("USER_SERVICE_JWT_SECRET_KEY") or _read_env_value(
        "JWT_SECRET_KEY"
    )
    if file_secret:
        return file_secret

    return _DEFAULT_JWT_SECRET


def _align_gateway_secret_with_user_service() -> None:
    settings.jwt_secret_key = _resolve_user_service_secret()


@pytest.mark.e2e
def test_gateway_register_login_profile_flow(client_with_mocks: TestClient) -> None:
    _align_gateway_secret_with_user_service()
    if not _is_user_service_ready(settings.user_service_url):
        pytest.skip(f"User Service not available at {settings.user_service_url}")

    email = f"user-{uuid4()}@example.com"
    password = "SecurePass123"

    register_response = client_with_mocks.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert register_response.status_code == 201

    login_response = client_with_mocks.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    profile_response = client_with_mocks.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email
