"""Payment Service application entrypoint."""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config import settings
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import payments


def create_app() -> FastAPI:
    """Create configured FastAPI application."""
    app = FastAPI(
        title="Payment Service API",
        description="Payment reservations for order saga",
        version="0.1.0",
        debug=settings.debug,
    )

    register_exception_handlers(app)
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
