from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

# Password hashing
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(_pwd_context.verify(plain_password, hashed_password))


def create_access_token(
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create an access JWT."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token: str | bytes = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token.decode("utf-8") if isinstance(token, bytes) else token


def create_refresh_token(
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_days: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a refresh JWT."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=expires_days)).timestamp()),
        "typ": "refresh",
    }
    if extra_claims:
        payload.update(extra_claims)
    token: str | bytes = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decode_token(token: str, secret_key: str, algorithms: list[str]) -> dict[str, Any]:
    """Decode and validate a JWT."""
    payload = jwt.decode(token, secret_key, algorithms=algorithms)
    return dict(payload)
