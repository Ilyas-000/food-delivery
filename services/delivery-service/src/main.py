"""Delivery Service application entrypoint."""

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
from src.interface.api.v1.routes import deliveries
from src.interface.api.ws import order_tracking
from src.interface.dependencies.delivery import get_order_tracking_broadcaster_instance


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage app startup/shutdown resources."""
    await init_event_publisher()
    yield
    await shutdown_event_publisher()
    broadcaster = get_order_tracking_broadcaster_instance()
    await broadcaster.close()


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Delivery Service API",
        description="Courier assignments for order saga",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(deliveries.router, prefix=settings.api_prefix)
    app.include_router(order_tracking.router)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
        kafka_status = "disabled"
        if settings.kafka_enabled:
            kafka_status = "healthy" if is_event_publisher_ready() else "unhealthy"

        overall_status = "healthy"
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
                    "kafka": kafka_status,
                },
            },
        )

    return app


app = create_app()
