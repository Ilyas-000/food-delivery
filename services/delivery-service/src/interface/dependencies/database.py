"""Database dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.infrastructure.database import base
from src.infrastructure.database.repositories.sqlalchemy_assignment_repository import (
    SqlAlchemyAssignmentRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    if base.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call create_async_session_maker() first.")

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_assignment_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IAssignmentRepository:
    """Provide assignment repository implementation."""
    return SqlAlchemyAssignmentRepository(session)
