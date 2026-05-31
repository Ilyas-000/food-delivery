"""Review service application entrypoint."""

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
from src.interface.api.v1.routes import reviews

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
    """Manage startup and shutdown lifecycle."""
    logger.info("service.starting", service=settings.service_name, environment=settings.environment)
    base.AsyncSessionLocal = base.create_async_session_maker(settings.database_url)
    await init_event_publisher()
    yield
    base.AsyncSessionLocal = None
    await shutdown_event_publisher()
    logger.info("service.stopped", service=settings.service_name)


async def _check_database_dependency() -> str:
    """Check database reachability."""
    if base.AsyncSessionLocal is None:
        return "not_initialized"
    try:
        async with base.AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - defensive health path
        logger.warning("health.database.unhealthy", error=str(exc))
        return "unhealthy"
    return "healthy"


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Review Service API",
        description="Restaurant reviews and ratings",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    metrics = ServiceMetrics(settings.service_name)
    app.state.reviews_created_total = metrics.create_counter(
        "food_delivery_reviews_created_total",
        "Number of successfully created reviews.",
        labelnames=("target_type", "result"),
    )

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

    register_exception_handlers(app)
    app.include_router(reviews.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Return service health."""
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
