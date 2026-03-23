"""Database dependencies for Order Service."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import base


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    if base.AsyncSessionLocal is None:
        raise RuntimeError("Database is not initialized")

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_optional_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Provide optional database session for backend-switched dependencies."""
    if base.AsyncSessionLocal is None:
        yield None
        return

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
