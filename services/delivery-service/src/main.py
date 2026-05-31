"""Delivery Service application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

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
from src.interface.api.v1.routes import deliveries
from src.interface.api.ws import order_tracking
from src.interface.dependencies.delivery import get_order_tracking_broadcaster_instance


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage app startup/shutdown resources."""
    base.AsyncSessionLocal = base.create_async_session_maker(settings.database_url)
    await init_event_publisher()
    yield
    base.AsyncSessionLocal = None
    await shutdown_event_publisher()
    broadcaster = get_order_tracking_broadcaster_instance()
    await broadcaster.close()


async def _check_database_dependency() -> str:
    """Check database reachability."""
    if base.AsyncSessionLocal is None:
        return "not_initialized"
    try:
        async with base.AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - defensive health path
        return "unhealthy"
    return "healthy"


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Delivery Service API",
        description="Courier assignments for order saga",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)
    app.state.delivery_assignments_total = metrics.create_counter(
        "food_delivery_delivery_assignments_total",
        "Number of successful courier assignments.",
        labelnames=("result",),
    )
    app.state.delivery_location_updates_total = metrics.create_counter(
        "food_delivery_delivery_location_updates_total",
        "Number of successful delivery location updates.",
        labelnames=("result",),
    )
    app.state.deliveries_completed_total = metrics.create_counter(
        "food_delivery_deliveries_completed_total",
        "Number of successfully completed deliveries.",
        labelnames=("result",),
    )

    register_exception_handlers(app)
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)
    app.include_router(deliveries.router, prefix=settings.api_prefix)
    app.include_router(order_tracking.router)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
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
                    "kafka": kafka_status,
                },
            },
        )

    return app


app = create_app()
