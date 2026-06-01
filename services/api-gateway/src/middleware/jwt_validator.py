"""JWT validation middleware and dependency."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

import jwt
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.common.jwt import decode_token

from src.config import settings

JWT_ALGORITHM = "HS256"

security = HTTPBearer()
logger = structlog.get_logger()


class JWTPayload:
    """Decoded JWT payload."""

    def __init__(self, user_id: str, role: str, email: str | None = None) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role


class OptionalAuthStatus(str, Enum):
    """Outcome of optional authentication."""

    ANONYMOUS = "anonymous"  # no (or malformed) Authorization header
    AUTHENTICATED = "authenticated"  # valid access token
    INVALID = "invalid"  # token present but expired/invalid/missing claims


@dataclass(frozen=True)
class OptionalAuth:
    """Result of optional authentication with explicit status.

    Distinguishes "no credentials" from "bad credentials" so public endpoints
    can stay permissive while diagnostics and audit logs keep precision.
    """

    status: OptionalAuthStatus
    user: JWTPayload | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.status is OptionalAuthStatus.AUTHENTICATED


def _decode_access_token(token: str) -> OptionalAuth:
    """Decode an optional access token into an authenticated/invalid result."""
    try:
        payload = decode_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        token_type = payload.get("type")

        if user_id and role and token_type == "access":  # nosec B105
            return OptionalAuth(
                status=OptionalAuthStatus.AUTHENTICATED,
                user=JWTPayload(user_id=user_id, role=role, email=email),
            )

        logger.debug(
            "Optional auth rejected token",
            reason="missing_claims_or_wrong_type",
            has_user_id=bool(user_id),
            has_role=bool(role),
            token_type=token_type,
        )
        return OptionalAuth(status=OptionalAuthStatus.INVALID)
    except jwt.ExpiredSignatureError as err:
        logger.debug("Optional auth token rejected", reason="expired", error=str(err))
        return OptionalAuth(status=OptionalAuthStatus.INVALID)
    except jwt.InvalidTokenError as err:
        logger.debug("Optional auth token rejected", reason="invalid", error=str(err))
        return OptionalAuth(status=OptionalAuthStatus.INVALID)


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JWTPayload:
    """Validate JWT token and extract user info."""
    token = credentials.credentials

    try:
        payload = decode_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as err:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"}},
        ) from err
    except jwt.InvalidTokenError as err:
        logger.warning("Invalid JWT token", error=str(err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token"}},
        ) from err

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")
    token_type = payload.get("type")

    if not user_id or not role:
        logger.warning(
            "JWT token missing required claims",
            has_user_id=bool(user_id),
            has_role=bool(role),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Missing required claims"}},
        )

    if token_type != "access":  # nosec B105
        logger.warning("JWT token has invalid type", user_id=user_id, token_type=token_type)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token type"}},
        )

    if not email:
        logger.info("JWT token missing email claim", user_id=user_id)

    return JWTPayload(user_id=user_id, role=role, email=email)


def require_role(*allowed_roles: str) -> Callable[..., Awaitable[JWTPayload]]:
    """Check if user has one of the allowed roles."""

    async def role_checker(user: JWTPayload = Depends(verify_jwt_token)) -> JWTPayload:
        if user.role not in allowed_roles:
            logger.warning(
                "JWT role check denied",
                user_id=user.user_id,
                role=user.role,
                allowed_roles=allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Required roles: {', '.join(allowed_roles)}",
                    }
                },
            )
        return user

    return role_checker


def get_optional_auth(request: Request) -> OptionalAuth:
    """Resolve optional auth into anonymous / authenticated / invalid."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return OptionalAuth(status=OptionalAuthStatus.ANONYMOUS)

    return _decode_access_token(auth_header[7:])


def get_optional_user(request: Request) -> JWTPayload | None:
    """Extract user from request if authenticated (optional).

    Backward-compatible accessor; use `get_optional_auth` when the caller needs
    to distinguish anonymous requests from invalid credentials.
    """
    return get_optional_auth(request).user
