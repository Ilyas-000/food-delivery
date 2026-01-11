"""JWT validation middleware and dependency.

The API Gateway validates JWT tokens to avoid forwarding
unauthorized requests to backend services.
"""

from collections.abc import Awaitable, Callable

import jwt
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.common.jwt import decode_token

from ..config import settings

security = HTTPBearer()
logger = structlog.get_logger()


class JWTPayload:
    """Decoded JWT payload."""

    def __init__(self, user_id: str, email: str, role: str) -> None:
        """Initialize JWT payload.

        Args:
            user_id: User UUID
            email: User email
            role: User role (customer, courier, restaurant_owner, admin)
        """
        self.user_id = user_id
        self.email = email
        self.role = role


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JWTPayload:
    """Validate JWT token and extract user info.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        JWTPayload: Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Decode and verify token
        payload = decode_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Extract claims
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        token_type = payload.get("type")

        if not user_id or not email or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Token is missing required claims",
                    }
                },
            )
        if token_type != "access":  # nosec B105
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid token type",
                    }
                },
            )

        return JWTPayload(user_id=user_id, email=email, role=role)

    except jwt.ExpiredSignatureError as err:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired. Please refresh your token.",
                }
            },
        ) from err
    except jwt.InvalidTokenError as err:
        logger.warning("Invalid JWT token", error=str(err))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Invalid authentication token",
                }
            },
        ) from err


def require_role(
    *allowed_roles: str,
) -> Callable[..., Awaitable[JWTPayload]]:
    """Check if user has one of the allowed roles.

    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: JWTPayload = Depends(require_role("admin"))):
            ...

    Args:
        allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function
    """

    async def role_checker(user: JWTPayload = Depends(verify_jwt_token)) -> JWTPayload:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Access denied. Required roles: {', '.join(allowed_roles)}",
                    }
                },
            )
        return user

    return role_checker


def get_optional_user(request: Request) -> JWTPayload | None:
    """Extract user from request if authenticated (optional).

    This is used by rate limiter to get user info without requiring auth.

    Args:
        request: FastAPI request

    Returns:
        JWTPayload if token is valid, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix

    try:
        payload = decode_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        if user_id and email and role and payload.get("type") == "access":  # nosec B105
            return JWTPayload(user_id=user_id, email=email, role=role)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        pass

    return None
