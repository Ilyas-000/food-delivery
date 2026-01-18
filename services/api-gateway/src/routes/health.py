"""Health check endpoints."""

import httpx
import structlog
from fastapi import APIRouter, status
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
        "service": "api-gateway",
        "version": "1.0.0",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> JSONResponse:
    """Readiness check - gateway and dependencies are ready.

    Checks:
    - Redis connection (for rate limiting)
    - User Service availability
    """
    checks = {
        "redis": "unknown",
        "user_service": "unknown",
    }
    all_healthy = True

    # Check Redis
    try:
        redis = get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        checks["redis"] = "unhealthy"
        all_healthy = False

    # Check User Service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.user_service_url}/health")
            if response.status_code == 200:
                checks["user_service"] = "healthy"
            else:
                checks["user_service"] = "unhealthy"
                all_healthy = False
    except Exception as e:
        logger.error("User Service health check failed", error=str(e))
        checks["user_service"] = "unhealthy"
        all_healthy = False

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "service": "api-gateway",
            "dependencies": checks,
        },
    )
