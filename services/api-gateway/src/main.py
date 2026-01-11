"""API Gateway - Single entry point for all microservices."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .deps.redis import close_redis, init_redis
from .middleware.circuit_breaker import CircuitBreakerMiddleware
from .middleware.logging import RequestLoggingMiddleware
from .routes import health, proxy


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

    # Initialize Redis for rate limiting
    if settings.rate_limit_enabled:
        await init_redis()
        logger.info("Redis connected for rate limiting")

    yield

    # Shutdown
    logger.info("Shutting down API Gateway")
    await close_redis()
    logger.info("Redis connection closed")


# Create FastAPI app
app = FastAPI(
    title="Food Delivery API Gateway",
    description="Single entry point for all microservices",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

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

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(proxy.router, tags=["Proxy"])
