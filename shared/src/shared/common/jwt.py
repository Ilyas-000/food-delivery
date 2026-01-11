"""
JWT utilities for authentication across services.

This is shared because:
- API Gateway validates tokens
- All services may need to decode tokens
- JWT format must be consistent across services

Password hashing is NOT here - each service implements its own.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


def create_access_token(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 30,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create an access JWT token.

    Args:
        subject: User ID or identifier (stored in 'sub' claim)
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default HS256)
        expires_minutes: Token lifetime in minutes
        extra_claims: Additional claims (e.g., role, permissions)

    Returns:
        str: Encoded JWT token

    Example:
        token = create_access_token(
            subject=str(user.id),
            secret_key="secret",
            extra_claims={"role": "customer"}
        )
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def create_refresh_token(
    subject: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_days: int = 7,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a refresh JWT token.

    Args:
        subject: User ID or identifier
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default HS256)
        expires_days: Token lifetime in days
        extra_claims: Additional claims

    Returns:
        str: Encoded JWT token

    Example:
        refresh = create_refresh_token(
            subject=str(user.id),
            secret_key="secret",
            expires_days=7
        )
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=expires_days)).timestamp()),
        "type": "refresh",
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def decode_token(
    token: str,
    secret_key: str,
    algorithms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithms: Allowed algorithms (default ["HS256"])

    Returns:
        dict: Decoded payload

    Raises:
        jwt.ExpiredSignatureError: If token expired
        jwt.InvalidTokenError: If token invalid

    Example:
        try:
            payload = decode_token(token, secret_key)
            user_id = payload["sub"]
        except jwt.ExpiredSignatureError:
            # Token expired
            pass
    """
    if algorithms is None:
        algorithms = ["HS256"]

    payload = jwt.decode(token, secret_key, algorithms=algorithms)
    return dict(payload)


def decode_token_unverified(token: str) -> dict[str, Any]:
    """
    Decode a JWT token without verifying signature or expiration.

    Use only for non-security decisions (e.g., rate limiting).

    Args:
        token: JWT token string

    Returns:
        dict: Decoded payload (unverified)
    """
    payload = jwt.decode(
        token,
        options={"verify_signature": False, "verify_exp": False},
    )
    return dict(payload)
