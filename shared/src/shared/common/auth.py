from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


def create_access_token(
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
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
    payload = jwt.decode(token, secret_key, algorithms=algorithms)
    return dict(payload)
