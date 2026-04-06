"""API Gateway - Single entry point for all microservices."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.config import settings
from src.dependencies.redis_client import close_redis, init_redis
from src.middleware.circuit_breaker import CircuitBreakerMiddleware
from src.middleware.logging import RequestLoggingMiddleware
from src.routes import health, proxy


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan (startup/shutdown)."""
    # Startup
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
            if settings.log_json
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper()),
    )

    logger = structlog.get_logger()
    logger.info(
        "Starting API Gateway",
        environment=settings.environment,
        port=settings.port,
    )

    # Initialize shared HTTP client for proxying
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.proxy_timeout_default),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        trust_env=False,
    )
    logger.info("HTTP client initialized")

    # Initialize Redis for rate limiting
    if settings.rate_limit_enabled:
        await init_redis()
        logger.info("Redis connected for rate limiting")

    yield

    # Shutdown
    logger.info("Shutting down API Gateway")
    http_client = getattr(app.state, "http_client", None)
    if http_client is not None:
        await http_client.aclose()
        logger.info("HTTP client closed")
    await close_redis()
    logger.info("Redis connection closed")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions with X-Request-ID for debugging."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Food Delivery API Gateway",
        description="Single entry point for all microservices",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Exception handlers
    app.add_exception_handler(Exception, global_exception_handler)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Custom middleware (order matters!)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CircuitBreakerMiddleware,
        failure_threshold=settings.circuit_breaker_failure_threshold,
        recovery_timeout=settings.circuit_breaker_recovery_timeout,
    )
    if settings.trust_proxy_headers:
        trusted_hosts = settings.trusted_proxy_ips or "*"
        # Add last so it runs first and sets request.client for downstream middleware.
        app.add_middleware(
            cast(Any, ProxyHeadersMiddleware),
            trusted_hosts=trusted_hosts,
        )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(proxy.router, tags=["Proxy"])

    return app


app = create_app()
