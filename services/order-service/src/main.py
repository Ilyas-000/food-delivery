"""Order Service application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
from src.interface.api.v1.routes import orders


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and dispose infrastructure resources."""
    if settings.repository_backend == "postgres":
        base.AsyncSessionLocal = base.create_async_session_maker(settings.database_url)
    await init_event_publisher()

    yield

    if settings.repository_backend == "postgres":
        base.AsyncSessionLocal = None
    await shutdown_event_publisher()


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Order Service API",
        description="Order orchestration and saga service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)
    app.state.order_created_total = metrics.create_counter(
        "food_delivery_order_created_total",
        "Number of successfully created orders.",
        labelnames=("result",),
    )

    register_exception_handlers(app)
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)
    app.include_router(orders.router, prefix=settings.api_prefix)

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
                "dependencies": {"kafka": kafka_status},
            },
        )

    return app


app = create_app()
