"""Integration test fixtures for restaurant-service."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import suppress

from fastapi import FastAPI
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
from src.infrastructure.database.models.menu_item_model import MenuItemModel
from src.infrastructure.database.models.restaurant_model import RestaurantModel
from src.interface.dependencies.database import get_db_session
from src.main import create_app


@pytest.fixture()
async def async_engine() -> AsyncIterator[AsyncEngine]:
    """Create async engine for test database."""
    test_db_url = settings.test_database_url
    if not test_db_url:
        pytest.skip("RESTAURANT_SERVICE_TEST_DATABASE_URL is not set")

    try:
        engine = create_async_engine(test_db_url, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        with suppress(Exception):
            await engine.dispose()
        pytest.skip(f"Test database unavailable: {exc}")

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test and clean up after."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.execute(delete(MenuItemModel))
            await session.execute(delete(RestaurantModel))
            await session.commit()


@pytest.fixture()
def restaurant_service_app(db_session: AsyncSession) -> FastAPI:
    """Create FastAPI app with test database session."""
    app = create_app()

    async def override_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_db_session

    return app


@pytest.fixture()
async def restaurant_service_client(
    restaurant_service_app: FastAPI,
) -> AsyncIterator[AsyncClient]:
    """Create async HTTP client for E2E tests."""
    transport = ASGITransport(app=restaurant_service_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://restaurant-service",
    ) as client:
        yield client
