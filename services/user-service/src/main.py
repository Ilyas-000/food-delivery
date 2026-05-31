"""
User Service - Main application entrypoint.

Этот модуль инициализирует FastAPI приложение, настраивает middleware,
регистрирует routes и обрабатывает lifecycle events (startup/shutdown).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC
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
from src.infrastructure.cache.redis_client import close_redis_client, create_redis_client
from src.infrastructure.database import base
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import auth, users

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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager для FastAPI приложения.

    Этот context manager управляет startup и shutdown событиями приложения.
    В startup мы инициализируем подключения к БД, Redis, Kafka и т.д.
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

    logger.info("Initializing Redis client")
    app.state.redis = create_redis_client()
    # TODO: Инициализация Kafka producer/consumer

    logger.info(f"{settings.service_name} started successfully")

    yield  # Приложение работает

    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.service_name}")

    # Закрытие Database connection pool
    if base.AsyncSessionLocal is not None:
        logger.info("Closing database connection pool")
        base.AsyncSessionLocal = None

    logger.info("Closing Redis client")
    if hasattr(app.state, "redis"):
        await close_redis_client(app.state.redis)
        app.state.redis = None
    # TODO: Закрытие Kafka producer/consumer

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


async def _check_redis_dependency(app: FastAPI) -> str:
    """Check that Redis client is reachable."""
    redis_client = getattr(app.state, "redis", None)
    if redis_client is None:
        return "not_initialized"

    try:
        is_alive = await redis_client.ping()
    except Exception as exc:  # pragma: no cover - defensive health path
        logger.warning("health.redis.unhealthy", error=str(exc))
        return "unhealthy"
    else:
        return "healthy" if is_alive else "unhealthy"


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
        title="User Service API",
        description="Authentication and user profile management service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)

    # === MIDDLEWARE ===

    # CORS Middleware (должен быть первым)
    # В продакшене CORS настройки должны быть более строгими
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

    # TODO: Request ID middleware (для distributed tracing)
    # TODO: Logging middleware (логирование всех requests)

    # === EXCEPTION HANDLERS ===
    # Register domain exception handlers BEFORE routes
    # This maps domain exceptions to HTTP responses
    register_exception_handlers(app)

    # === ROUTES ===

    # Register API v1 routes
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)

    # Health check endpoint (не требует аутентификации)
    # Format follows docs/API_CONVENTIONS.md
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str | dict[str, str]]:
        """
        Health check endpoint following API_CONVENTIONS.md format.

        Используется для:
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Monitoring systems

        Returns:
            dict: Health status with version, timestamp, and dependencies

        Response format (API_CONVENTIONS.md):
            {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2026-01-08T...",
                "dependencies": {
                    "database": "healthy",
                    "redis": "not_configured",
                    "kafka": "not_configured"
                }
            }
        """
        from datetime import datetime

        database_status = await _check_database_dependency()
        redis_status = await _check_redis_dependency(app)
        dependencies = {
            "database": database_status,
            "redis": redis_status,
            "kafka": "not_configured",
        }

        overall_status = "healthy"
        if database_status != "healthy" or redis_status != "healthy":
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "version": "0.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "dependencies": dependencies,
        }

    # === GLOBAL EXCEPTION HANDLER ===

    @app.exception_handler(Exception)
    async def global_exception_handler(_request, exc: Exception) -> JSONResponse:  # type: ignore[no-untyped-def]
        """
        Глобальный обработчик исключений following API_CONVENTIONS.md.

        В продакшене не должны возвращаться детали ошибки пользователю.
        Вместо этого логируем ошибку и возвращаем generic message.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSONResponse: Error response in standard format
        """
        from datetime import datetime
        import uuid

        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        # В development показываем детали ошибки
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal Server Error",
                        "details": {
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                        },
                        "request_id": str(uuid.uuid4()),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                },
            )

        # В production возвращаем generic ошибку
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal Server Error",
                    "details": {},
                    "request_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            },
        )

    return app


# Создаем приложение
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Запуск для локальной разработки
    # В продакшене используем: uvicorn src.main:app --host 0.0.0.0 --port 8001
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
