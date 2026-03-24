"""Order Service application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config import settings
from src.infrastructure.database import base
from src.interface.api.exception_handlers import register_exception_handlers
from src.interface.api.v1.routes import orders


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and dispose infrastructure resources."""
    if settings.repository_backend == "postgres":
        base.AsyncSessionLocal = base.create_async_session_maker(settings.database_url)

    yield

    if settings.repository_backend == "postgres":
        base.AsyncSessionLocal = None


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

    register_exception_handlers(app)
    app.include_router(orders.router, prefix=settings.api_prefix)

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
