"""Integration fixtures for order-service.

These tests run order-service in postgres + http saga mode.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import suppress

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.infrastructure.database.base import Base
from src.infrastructure.database.models.order_model import OrderItemModel, OrderModel
from src.interface.dependencies import order as order_dependencies
from src.interface.dependencies.database import get_optional_db_session
from src.main import create_app


@pytest.fixture()
async def async_engine() -> AsyncIterator[AsyncEngine]:
    """Create async engine for isolated order-service integration database."""
    test_db_url = settings.test_database_url
    if not test_db_url:
        pytest.skip("ORDER_SERVICE_TEST_DATABASE_URL is not set")

    try:
        engine = create_async_engine(test_db_url, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        with suppress(Exception):
            await engine.dispose()
        pytest.skip(f"Order test database unavailable: {exc}")

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide per-test DB session and cleanup persisted orders."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.execute(delete(OrderItemModel))
            await session.execute(delete(OrderModel))
            await session.commit()


@pytest.fixture()
async def _require_http_saga_dependencies() -> None:
    """Skip integration tests when external saga services are unavailable."""
    health_urls = (
        f"{settings.restaurant_service_url}/health",
        f"{settings.payment_service_url}/health",
        f"{settings.delivery_service_url}/health",
    )
    try:
        async with AsyncClient(timeout=5.0) as client:
            for url in health_urls:
                response = await client.get(url)
                if response.status_code != status.HTTP_200_OK:
                    pytest.skip(f"Dependency health check failed: {url} -> {response.status_code}")
    except Exception as exc:
        pytest.skip(f"HTTP saga dependencies are unavailable: {exc}")


@pytest.fixture()
def order_service_app(
    monkeypatch: pytest.MonkeyPatch,
    db_session: AsyncSession,
    _require_http_saga_dependencies: None,
) -> FastAPI:
    """Create order-service app wired for postgres + http saga integration mode."""
    monkeypatch.setattr(order_dependencies.settings, "repository_backend", "postgres")
    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "http")

    app = create_app()

    async def override_optional_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_optional_db_session] = override_optional_db_session
    return app


@pytest.fixture()
async def order_service_client(order_service_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """HTTP client for order-service integration tests."""
    transport = ASGITransport(app=order_service_app)
    async with AsyncClient(transport=transport, base_url="http://order-service") as client:
        yield client
