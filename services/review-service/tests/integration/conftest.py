"""Integration fixtures for review-service."""

from collections.abc import AsyncGenerator, AsyncIterator
from uuid import UUID

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

from src.application.dto.review import DeliverySnapshotDTO, OrderSnapshotDTO
from src.application.interfaces.validation_clients import (
    IDeliveryValidationClient,
    IOrderValidationClient,
)
from src.config import settings
from src.infrastructure.database.base import Base
from src.infrastructure.database.models.review_model import ReviewModel
from src.interface.dependencies.database import get_db_session
from src.interface.dependencies.review import (
    get_delivery_validation_client,
    get_order_validation_client,
)
from src.main import create_app


class StubOrderValidationClient(IOrderValidationClient):
    """Stub order client for integration tests."""

    async def get_order(self, order_id: UUID) -> OrderSnapshotDTO:
        return OrderSnapshotDTO(
            order_id=order_id,
            user_id=UUID("11111111-1111-1111-1111-111111111111"),
            restaurant_id=UUID("22222222-2222-2222-2222-222222222222"),
            status="confirmed",
        )


class StubDeliveryValidationClient(IDeliveryValidationClient):
    """Stub delivery client for integration tests."""

    async def get_delivery(self, order_id: UUID) -> DeliverySnapshotDTO:
        return DeliverySnapshotDTO(
            assignment_id=UUID("33333333-3333-3333-3333-333333333333"),
            order_id=order_id,
            restaurant_id=UUID("22222222-2222-2222-2222-222222222222"),
            courier_id=UUID("44444444-4444-4444-4444-444444444444"),
            status="completed",
            delivered_at=None,
        )


@pytest.fixture()
async def async_engine() -> AsyncIterator[AsyncEngine]:
    """Create async engine for isolated test database."""
    test_db_url = settings.test_database_url
    if not test_db_url:
        pytest.skip("REVIEW_SERVICE_TEST_DATABASE_URL is not set")

    engine = create_async_engine(test_db_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide transaction-scoped session."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.execute(delete(ReviewModel))
            await session.commit()


@pytest.fixture()
def review_service_app(db_session: AsyncSession) -> FastAPI:
    """Create app with overridden dependencies."""
    app = create_app()

    async def override_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_order_client() -> IOrderValidationClient:
        return StubOrderValidationClient()

    async def override_delivery_client() -> IDeliveryValidationClient:
        return StubDeliveryValidationClient()

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_order_validation_client] = override_order_client
    app.dependency_overrides[get_delivery_validation_client] = override_delivery_client
    return app


@pytest.fixture()
async def review_service_client(review_service_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Create async HTTP client for integration tests."""
    transport = ASGITransport(app=review_service_app)
    async with AsyncClient(transport=transport, base_url="http://review-service") as client:
        yield client
