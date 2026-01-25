from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import suppress
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

from src.application.interfaces.password_hasher import IPasswordHasher
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.config import settings
from src.infrastructure.database.base import Base
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.security.password_hasher import PasswordHasher
from src.interface.dependencies.auth import get_password_hasher
from src.interface.dependencies.database import get_db_session
from src.interface.dependencies.refresh_token_repository import get_refresh_token_repository
from src.main import create_app


class InMemoryRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self) -> None:
        self._active: set[str] = set()

    async def store(self, jti: str, user_id: UUID, expires_in: int) -> None:
        _ = user_id
        _ = expires_in
        self._active.add(jti)

    async def exists(self, jti: str) -> bool:
        return jti in self._active

    async def delete(self, jti: str) -> None:
        self._active.discard(jti)


@pytest.fixture(scope="session")
async def async_engine() -> AsyncIterator[AsyncEngine]:
    test_db_url = settings.test_database_url
    if not test_db_url:
        pytest.skip("USER_SERVICE_TEST_DATABASE_URL is not set")

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
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.execute(delete(UserModel))
            await session.commit()


@pytest.fixture()
def refresh_token_repository() -> InMemoryRefreshTokenRepository:
    return InMemoryRefreshTokenRepository()


@pytest.fixture()
def user_service_app(
    db_session: AsyncSession,
    refresh_token_repository: InMemoryRefreshTokenRepository,
) -> FastAPI:
    app = create_app()

    async def override_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_refresh_token_repository() -> IRefreshTokenRepository:
        return refresh_token_repository

    async def override_password_hasher() -> IPasswordHasher:
        return PasswordHasher(rounds=4)

    overrides = app.dependency_overrides
    overrides[get_db_session] = override_db_session
    overrides[get_refresh_token_repository] = override_refresh_token_repository
    overrides[get_password_hasher] = override_password_hasher

    return app


@pytest.fixture()
async def user_service_client(user_service_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=user_service_app)
    async with AsyncClient(transport=transport, base_url="http://user-service") as client:
        yield client
