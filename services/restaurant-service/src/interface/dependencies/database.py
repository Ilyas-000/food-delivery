"""Database dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.infrastructure.database import base
from src.infrastructure.database.repositories.menu_item_repository import MenuItemRepository
from src.infrastructure.database.repositories.restaurant_repository import RestaurantRepository


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    if base.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call create_async_session_maker() first.")

    async with base.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_restaurant_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IRestaurantRepository:
    """Provide RestaurantRepository."""
    return RestaurantRepository(session)


async def get_menu_item_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IMenuItemRepository:
    """Provide MenuItemRepository."""
    return MenuItemRepository(session)
