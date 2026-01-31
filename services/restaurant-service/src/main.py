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
import structlog

from src.config import settings
from src.infrastructure.database import base

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
    # TODO: Инициализация Kafka producer для событий

    logger.info(f"{settings.service_name} started successfully")

    yield  # Приложение работает

    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.service_name}")

    # Закрытие Database connection pool
    if base.AsyncSessionLocal is not None:
        logger.info("Closing database connection pool")
        base.AsyncSessionLocal = None

    # TODO: Закрытие Redis client
    # TODO: Закрытие Kafka producer

    logger.info(f"{settings.service_name} shutdown complete")


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

    # === MIDDLEWARE ===

    # CORS Middleware (разрешает frontend запросы)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # === EXCEPTION HANDLERS ===
    # TODO: Register domain exception handlers when implemented

    # === ROUTES ===
    # TODO: Include restaurant routes when implemented
    # TODO: Include menu-items routes when implemented

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
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": settings.service_name,
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": settings.environment,
                "dependencies": {
                    "database": "healthy" if base.AsyncSessionLocal else "not_initialized",
                    # TODO: Check Redis health
                    # TODO: Check Kafka health
                },
            },
        )

    return app


# Create app instance (import this in uvicorn command)
app = create_app()
