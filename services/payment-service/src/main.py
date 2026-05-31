"""Payment Service application entrypoint."""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from shared.observability.prometheus import ServiceMetrics, install_prometheus
from shared.observability.request_context import install_request_context
from src.config import settings
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import payments


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Payment Service API",
        description="Payment lifecycle service for order saga",
        version="0.1.0",
        debug=settings.debug,
    )
    metrics = ServiceMetrics(settings.service_name)
    app.state.payment_reservations_total = metrics.create_counter(
        "food_delivery_payment_reservations_total",
        "Number of successful payment reservations.",
        labelnames=("result",),
    )
    app.state.payment_confirmations_total = metrics.create_counter(
        "food_delivery_payment_confirmations_total",
        "Number of successful payment confirmations.",
        labelnames=("result",),
    )
    app.state.payment_refunds_total = metrics.create_counter(
        "food_delivery_payment_refunds_total",
        "Number of successful payment refunds.",
        labelnames=("result",),
    )

    register_exception_handlers(app)
    if settings.metrics_enabled:
        install_prometheus(app, metrics, metrics_path=settings.metrics_path)
    install_request_context(app, service_name=settings.service_name)
    app.include_router(payments.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": settings.service_name,
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
                "environment": settings.environment,
            },
        )

    return app


app = create_app()
