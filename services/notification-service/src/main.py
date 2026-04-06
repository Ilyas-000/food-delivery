"""Notification Service application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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

    register_exception_handlers(app)
    app.include_router(notifications.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
        consumer = get_notification_event_consumer()
        kafka_producer_status = "disabled"
        kafka_consumer_status = "disabled"

        if settings.kafka_enabled:
            kafka_producer_status = "healthy" if is_event_publisher_ready() else "unhealthy"
            kafka_consumer_status = "healthy" if consumer.is_ready() else "unhealthy"

        overall_status = "healthy"
        if settings.kafka_enabled and (
            kafka_producer_status != "healthy" or kafka_consumer_status != "healthy"
        ):
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
                    "kafka_producer": kafka_producer_status,
                    "kafka_consumer": kafka_consumer_status,
                },
            },
        )

    return app


app = create_app()
