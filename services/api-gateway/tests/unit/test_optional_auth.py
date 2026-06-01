"""Unit tests for optional auth status semantics."""

from types import SimpleNamespace

import pytest
from shared.common.jwt import create_access_token

from src.config import settings
from src.middleware.jwt_validator import (
    OptionalAuthStatus,
    get_optional_auth,
    get_optional_user,
)


def _request(authorization: str | None = None) -> SimpleNamespace:
    headers = {"Authorization": authorization} if authorization is not None else {}
    return SimpleNamespace(headers=headers)


def _valid_token() -> str:
    return create_access_token(
        subject="user-123",
        secret_key=settings.jwt_secret_key,
        extra_claims={"role": "customer", "email": "user@example.com"},
    )


@pytest.mark.unit
def test_missing_header_is_anonymous() -> None:
    result = get_optional_auth(_request())

    assert result.status is OptionalAuthStatus.ANONYMOUS
    assert result.user is None
    assert result.is_authenticated is False


@pytest.mark.unit
def test_non_bearer_header_is_anonymous() -> None:
    result = get_optional_auth(_request("Basic abc123"))

    assert result.status is OptionalAuthStatus.ANONYMOUS
    assert result.user is None


@pytest.mark.unit
def test_valid_token_is_authenticated() -> None:
    result = get_optional_auth(_request(f"Bearer {_valid_token()}"))

    assert result.status is OptionalAuthStatus.AUTHENTICATED
    assert result.is_authenticated is True
    assert result.user is not None
    assert result.user.user_id == "user-123"
    assert result.user.role == "customer"


@pytest.mark.unit
def test_garbage_token_is_invalid() -> None:
    result = get_optional_auth(_request("Bearer not-a-real-jwt"))

    assert result.status is OptionalAuthStatus.INVALID
    assert result.user is None
    assert result.is_authenticated is False


@pytest.mark.unit
def test_wrong_secret_signature_is_invalid() -> None:
    token = create_access_token(
        subject="user-123",
        secret_key="a-different-secret-key",
        extra_claims={"role": "customer"},
    )

    result = get_optional_auth(_request(f"Bearer {token}"))

    assert result.status is OptionalAuthStatus.INVALID


@pytest.mark.unit
def test_refresh_token_type_is_invalid() -> None:
    token = create_access_token(
        subject="user-123",
        secret_key=settings.jwt_secret_key,
        extra_claims={"role": "customer", "type": "refresh"},
    )

    result = get_optional_auth(_request(f"Bearer {token}"))

    assert result.status is OptionalAuthStatus.INVALID


@pytest.mark.unit
def test_get_optional_user_stays_backward_compatible() -> None:
    assert get_optional_user(_request()) is None

    user = get_optional_user(_request(f"Bearer {_valid_token()}"))
    assert user is not None
    assert user.user_id == "user-123"
