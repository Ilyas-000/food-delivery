"""Database dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.review_repository import IReviewRepository
from src.infrastructure.database import base
from src.infrastructure.database.repositories.review_repository import ReviewRepository


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    if base.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call create_async_session_maker() first.")

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_review_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IReviewRepository:
    """Provide repository implementation."""
    return ReviewRepository(session)
