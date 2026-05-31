"""Health check endpoints."""

import httpx
import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.dependencies.redis_client import get_redis

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Basic health check - gateway is running."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(request: Request) -> JSONResponse:
    """Readiness check - gateway and dependencies are ready.

    Checks:
    - Redis connection (for rate limiting)
    - User Service availability
    - Order Service availability
    """
    checks = {
        "redis": "unknown",
        "user_service": "unknown",
        "order_service": "unknown",
    }
    all_healthy = True

    # Check Redis
    if settings.rate_limit_enabled:
        try:
            redis = get_redis()
            await redis.ping()
            checks["redis"] = "healthy"
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            checks["redis"] = "unhealthy"
            all_healthy = False
    else:
        checks["redis"] = "disabled"

    # Check User Service
    try:
        client = getattr(request.app.state, "http_client", None)
        if client is None:
            logger.warning("HTTP client not initialized; using temporary client")
            async with httpx.AsyncClient(timeout=5.0, trust_env=False) as temp_client:
                response = await temp_client.get(f"{settings.user_service_url}/health")
        else:
            response = await client.get(f"{settings.user_service_url}/health", timeout=5.0)

        if response.status_code == 200:
            checks["user_service"] = "healthy"
        else:
            checks["user_service"] = "unhealthy"
            all_healthy = False
    except Exception as e:
        logger.error("User Service health check failed", error=str(e))
        checks["user_service"] = "unhealthy"
        all_healthy = False

    # Check Order Service
    try:
        client = getattr(request.app.state, "http_client", None)
        if client is None:
            logger.warning("HTTP client not initialized; using temporary client")
            async with httpx.AsyncClient(timeout=5.0, trust_env=False) as temp_client:
                response = await temp_client.get(f"{settings.order_service_url}/health")
        else:
            response = await client.get(f"{settings.order_service_url}/health", timeout=5.0)

        if response.status_code == 200:
            checks["order_service"] = "healthy"
        else:
            checks["order_service"] = "unhealthy"
            all_healthy = False
    except Exception as e:
        logger.error("Order Service health check failed", error=str(e))
        checks["order_service"] = "unhealthy"
        all_healthy = False

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "service": settings.service_name,
            "dependencies": checks,
        },
    )
