"""
Restaurant Service - Main application entrypoint.

Этот модуль инициализирует FastAPI приложение, настраивает middleware,
регистрирует routes и обрабатывает lifecycle events (startup/shutdown).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import structlog

from shared.observability.prometheus import ServiceMetrics, install_prometheus
from shared.observability.request_context import install_request_context
from src.config import settings
from src.infrastructure.database import base
from src.infrastructure.events.publisher import (
    init_event_publisher,
    is_event_publisher_ready,
    shutdown_event_publisher,
)
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import restaurants

# Configure structlog (unified logging across all modules)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager для FastAPI приложения.

    Этот context manager управляет startup и shutdown событиями приложения.
    В startup мы инициализируем подключения к БД, Redis и т.д.
    В shutdown мы корректно закрываем все соединения.

    Args:
        app: FastAPI application instance

    Yields:
        None: Control flow during application lifetime
    """
    # === STARTUP ===
    logger.info(f"Starting {settings.service_name} in {settings.environment} environment")
    logger.info(f"API available at http://{settings.api_host}:{settings.api_port}")
    logger.info(f"API docs at http://{settings.api_host}:{settings.api_port}/docs")

    # Инициализация Database connection pool
    logger.info("Initializing database connection pool")
    base.AsyncSessionLocal = base.create_async_session_maker(settings.database_url)
    logger.info("Database connection pool initialized")

    # TODO: Инициализация Redis client для кеширования
    await init_event_publisher()

    logger.info(f"{settings.service_name} started successfully")

    yield  # Приложение работает

    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.service_name}")

    # Закрытие Database connection pool
    if base.AsyncSessionLocal is not None:
        logger.info("Closing database connection pool")
        base.AsyncSessionLocal = None

    # TODO: Закрытие Redis client
    await shutdown_event_publisher()

    logger.info(f"{settings.service_name} shutdown complete")


async def _check_database_dependency() -> str:
    """Check that database is reachable."""
    if base.AsyncSessionLocal is None:
        return "not_initialized"

    try:
        async with base.AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive health path
        logger.warning("health.database.unhealthy", error=str(exc))
        return "unhealthy"
    else:
        return "healthy"


def create_app() -> FastAPI:
    """
    Factory function для создания FastAPI приложения.

    Этот паттерн (Application Factory) позволяет:
    - Легко создавать приложение с разными настройками для тестов
    - Избегать глобального состояния
    - Упростить тестирование

    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title="Restaurant Service API",
        description="Restaurant and menu management service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)

    # === MIDDLEWARE ===

    # CORS Middleware (разрешает frontend запросы)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)

    # === EXCEPTION HANDLERS ===
    register_exception_handlers(app)

    # === ROUTES ===
    app.include_router(restaurants.router, prefix=settings.api_prefix)

    # Health check endpoint (для Kubernetes/Docker health checks)
    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """
        Health check endpoint.

        Used by:
        - Kubernetes liveness/readiness probes
        - Docker HEALTHCHECK
        - Load balancers
        - Monitoring systems

        Returns:
            JSONResponse: Service health status
        """
        database_status = await _check_database_dependency()
        kafka_status = "disabled"
        if settings.kafka_enabled:
            kafka_status = "healthy" if is_event_publisher_ready() else "unhealthy"

        overall_status = "healthy"
        if database_status != "healthy":
            overall_status = "unhealthy"
        if settings.kafka_enabled and kafka_status != "healthy":
            overall_status = "unhealthy"

        return JSONResponse(
            status_code=200,
            content={
                "status": overall_status,
                "service": settings.service_name,
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": settings.environment,
                "dependencies": {
                    "database": database_status,
                    "redis": "deferred",
                    "kafka": kafka_status,
                },
            },
        )

    return app


# Create app instance (import this in uvicorn command)
app = create_app()
