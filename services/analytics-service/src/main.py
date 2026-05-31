"""Analytics Service application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from shared.observability.prometheus import ServiceMetrics, install_prometheus
from shared.observability.request_context import install_request_context
from src.config import settings
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import analytics
from src.interface.dependencies.analytics import (
    get_analytics_event_consumer,
    get_analytics_repository_instance,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage app startup and shutdown resources."""
    repository = get_analytics_repository_instance()
    consumer = get_analytics_event_consumer()

    await repository.start()
    if settings.kafka_enabled:
        await consumer.start()

    yield

    await consumer.stop()
    await repository.stop()


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Analytics Service API",
        description="Operational analytics and reporting service",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)

    register_exception_handlers(app)
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)
    app.include_router(analytics.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Liveness check - the service process is running."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "service": settings.service_name,
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": settings.environment,
            },
        )

    @app.get("/ready", tags=["health"])
    async def readiness_check() -> JSONResponse:
        """Readiness check - storage and Kafka consumer are ready to ingest events."""
        repository = get_analytics_repository_instance()
        consumer = get_analytics_event_consumer()

        clickhouse_status = "healthy" if repository.is_ready() else "unhealthy"
        kafka_consumer_status = "disabled"
        ready = repository.is_ready()

        if settings.kafka_enabled:
            kafka_consumer_status = "healthy" if consumer.is_ready() else "unhealthy"
            if not consumer.is_ready():
                ready = False

        status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if ready else "not_ready",
                "service": settings.service_name,
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": settings.environment,
                "dependencies": {
                    "storage": settings.storage_backend,
                    "clickhouse": clickhouse_status,
                    "kafka_consumer": kafka_consumer_status,
                },
            },
        )

    return app


app = create_app()
