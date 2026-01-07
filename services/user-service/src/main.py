"""
User Service - Main application entrypoint.

Этот модуль инициализирует FastAPI приложение, настраивает middleware,
регистрирует routes и обрабатывает lifecycle events (startup/shutdown).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
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

    # TODO: Инициализация Database connection pool
    # TODO: Инициализация Redis connection
    # TODO: Инициализация Kafka producer/consumer

    logger.info(f"{settings.service_name} started successfully")

    yield  # Приложение работает

    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.service_name}")

    # TODO: Закрытие Database connection pool
    # TODO: Закрытие Redis connection
    # TODO: Закрытие Kafka producer/consumer

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
        title="User Service API",
        description="Authentication and user profile management service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )

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

    # TODO: Request ID middleware (для distributed tracing)
    # TODO: Logging middleware (логирование всех requests)
    # TODO: Exception handler middleware

    # === ROUTES ===

    # Health check endpoint (не требует аутентификации)
    @app.get("/health", tags=["Health"], response_model=dict[str, str])
    async def health_check() -> dict[str, str]:
        """
        Health check endpoint.

        Используется для:
        - Kubernetes liveness/readiness probes
        - Load balancer health checks
        - Monitoring systems

        В будущем здесь можно добавить проверки:
        - Подключение к БД
        - Подключение к Redis
        - Подключение к Kafka

        Returns:
            dict: Health status
        """
        return {
            "status": "ok",
            "service": settings.service_name,
            "environment": settings.environment,
        }

    # Readiness probe (более строгая проверка чем health)
    @app.get("/ready", tags=["Health"], response_model=dict[str, str | bool])
    async def readiness_check() -> dict[str, str | bool]:
        """
        Readiness check endpoint.

        Проверяет готовность сервиса к обработке запросов.
        В отличие от /health, здесь проверяем зависимости:
        - Database connectivity
        - Redis availability
        - External services

        Returns:
            dict: Readiness status with dependencies
        """
        # TODO: Проверить подключение к PostgreSQL
        # TODO: Проверить подключение к Redis
        # TODO: Проверить подключение к Kafka

        return {
            "status": "ready",
            "service": settings.service_name,
            "database": True,  # TODO: реальная проверка
            "redis": True,  # TODO: реальная проверка
        }

    # TODO: Регистрация API routes

    # === EXCEPTION HANDLERS ===

    @app.exception_handler(Exception)
    async def global_exception_handler(_request, exc: Exception) -> JSONResponse:  # type: ignore[no-untyped-def]
        """
        Глобальный обработчик исключений.

        В продакшене не должны возвращаться детали ошибки пользователю.
        Вместо этого логируем ошибку и возвращаем generic message.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSONResponse: Error response
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        # В development показываем детали ошибки
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc),
                    "type": type(exc).__name__,
                },
            )

        # В production возвращаем generic ошибку
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error"},
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
