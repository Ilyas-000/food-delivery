"""Notification Service application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from shared.observability.prometheus import ServiceMetrics, install_prometheus
from shared.observability.request_context import install_request_context
from src.config import settings
from src.infrastructure.events.publisher import (
    init_event_publisher,
    is_event_publisher_ready,
    shutdown_event_publisher,
)
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import notifications
from src.interface.dependencies.notification import get_notification_event_consumer


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage app startup and shutdown resources."""
    consumer = get_notification_event_consumer()
    await init_event_publisher()
    if settings.kafka_enabled:
        await consumer.start()

    yield

    await consumer.stop()
    await shutdown_event_publisher()


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Notification Service API",
        description="Event-driven notification delivery service",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)
    app.state.notifications_sent_total = metrics.create_counter(
        "food_delivery_notifications_sent_total",
        "Number of successfully sent notifications.",
        labelnames=("channel", "result"),
    )

    register_exception_handlers(app)
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)
    app.include_router(notifications.router, prefix=settings.api_prefix)

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
        """Readiness check - Kafka producer and consumer are ready to serve events."""
        consumer = get_notification_event_consumer()
        kafka_producer_status = "disabled"
        kafka_consumer_status = "disabled"
        ready = True

        if settings.kafka_enabled:
            kafka_producer_status = "healthy" if is_event_publisher_ready() else "unhealthy"
            kafka_consumer_status = "healthy" if consumer.is_ready() else "unhealthy"
            if kafka_producer_status != "healthy" or kafka_consumer_status != "healthy":
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
                    "kafka_producer": kafka_producer_status,
                    "kafka_consumer": kafka_consumer_status,
                },
            },
        )

    return app


app = create_app()
