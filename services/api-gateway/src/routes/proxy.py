"""Reverse proxy routes to backend services.

Routes requests from clients to appropriate microservices:
- /api/v1/auth/* -> User Service
- /api/v1/users/* -> User Service
- TODO: Add other services in future phases
"""

import httpx
import structlog
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from shared.common.jwt import decode_token_unverified

from ..config import settings
from ..deps.redis import get_redis
from ..middleware.jwt_validator import JWTPayload, verify_jwt_token
from ..middleware.rate_limiter import RateLimiter

router = APIRouter()
logger = structlog.get_logger()


async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    redis = get_redis()
    return RateLimiter(redis)


async def proxy_to_service(
    request: Request,
    service_url: str,
    path: str,
) -> Response:
    """Proxy request to backend service.

    Args:
        request: Incoming request
        service_url: Backend service URL
        path: Path to append to service URL

    Returns:
        Response from backend service
    """
    # Build target URL
    target_url = f"{service_url}/{path}"

    # Copy headers (exclude hop-by-hop headers)
    headers = dict(request.headers)
    excluded_headers = {
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
    }
    headers = {k: v for k, v in headers.items() if k.lower() not in excluded_headers}

    # Add request ID for tracing
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    try:
        # Forward request to backend service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params,
            )

        # Return response (preserve status code and headers)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.TimeoutException:
        logger.error("Service timeout", service=service_url, path=path)
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "GATEWAY_TIMEOUT",
                    "message": "Backend service timeout",
                }
            },
        )
    except httpx.NetworkError as e:
        logger.error("Network error", service=service_url, error=str(e))
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": "BAD_GATEWAY",
                    "message": "Failed to connect to backend service",
                }
            },
        )
    except Exception as e:
        logger.error("Proxy error", service=service_url, error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Gateway internal error",
                }
            },
        )


# ============================================================================
# AUTH ROUTES (Public - no JWT required)
# ============================================================================


@router.post("/api/v1/auth/register")
async def register(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Response:
    """Register new user (proxied to User Service).

    Rate limiting: Global auth limits apply.
    """
    # Apply global auth rate limiting
    await rate_limiter.check_auth_global_rate_limit(request)

    return await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/auth/register",
    )


@router.post("/api/v1/auth/login")
async def login(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Response:
    """Login user (proxied to User Service).

    Rate limiting:
    - Global auth limits
    - Login-specific limits (per IP, per account, per IP+account)
    - Progressive backoff on failures
    """
    # Apply global auth rate limiting
    await rate_limiter.check_auth_global_rate_limit(request)

    # Parse request body to get email (for per-account rate limiting)
    body = await request.body()
    try:
        import json

        data = json.loads(body) if body else {}
        email = data.get("email")
    except Exception:
        email = None

    # Apply login-specific rate limiting
    await rate_limiter.check_login_rate_limit(request, email)

    # Forward request
    response = await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/auth/login",
    )

    # Record failure if login failed (for progressive backoff)
    if response.status_code == 401:
        await rate_limiter.record_login_failure(request, email)

    return response


@router.post("/api/v1/auth/refresh")
async def refresh(
    request: Request,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> Response:
    """Refresh access token (proxied to User Service).

    Rate limiting:
    - Global auth limits
    - Refresh-specific limits (per JTI, per user, per IP)
    """
    # Apply global auth rate limiting
    await rate_limiter.check_auth_global_rate_limit(request)

    # Parse request body to get refresh token
    body = await request.body()
    try:
        import json

        data = json.loads(body) if body else {}
        refresh_token = data.get("refresh_token")
    except Exception:
        refresh_token = None

    # Apply refresh-specific rate limiting
    if refresh_token:
        # Try to extract user_id from token (without verification)
        try:
            unverified = decode_token_unverified(refresh_token)
            user_id = unverified.get("sub")
        except Exception:
            user_id = None

        await rate_limiter.check_refresh_rate_limit(request, refresh_token, user_id)

    return await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/auth/refresh",
    )


@router.post("/api/v1/auth/logout")
async def logout(
    request: Request,
    _user: JWTPayload = Depends(verify_jwt_token),  # Require authentication
) -> Response:
    """Logout user (proxied to User Service).

    Requires: Valid JWT token
    """
    return await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/auth/logout",
    )


# ============================================================================
# USER ROUTES (Protected - JWT required)
# ============================================================================


@router.get("/api/v1/users/me")
async def get_my_profile(
    request: Request,
    _user: JWTPayload = Depends(verify_jwt_token),  # Require authentication
) -> Response:
    """Get current user profile (proxied to User Service).

    Requires: Valid JWT token
    """
    return await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/users/me",
    )


@router.patch("/api/v1/users/me")
async def update_my_profile(
    request: Request,
    _user: JWTPayload = Depends(verify_jwt_token),  # Require authentication
) -> Response:
    """Update current user profile (proxied to User Service).

    Requires: Valid JWT token
    """
    return await proxy_to_service(
        request,
        settings.user_service_url,
        "api/v1/users/me",
    )


@router.get("/api/v1/users/{user_id}")
async def get_user_by_id(
    request: Request,
    user_id: str,
    _user: JWTPayload = Depends(verify_jwt_token),  # Require authentication
) -> Response:
    """Get user by ID (proxied to User Service).

    Requires: Valid JWT token (admin only in User Service)
    """
    return await proxy_to_service(
        request,
        settings.user_service_url,
        f"api/v1/users/{user_id}",
    )


# ============================================================================
# CATCH-ALL ROUTE (for future services)
# ============================================================================
# TODO: When adding new services (Restaurant, Order, etc.), add specific
# routes above or use a more sophisticated routing mechanism.
