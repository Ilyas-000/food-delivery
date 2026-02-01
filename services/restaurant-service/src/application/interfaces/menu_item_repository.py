"""
MenuItem Repository Interface.

Defines the contract for menu item persistence operations.
Infrastructure layer implements this interface.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import MenuItem
from src.domain.value_objects import Category


class IMenuItemRepository(ABC):
    """
    MenuItem repository interface.

    This interface defines all persistence operations for menu items.
    Infrastructure layer provides the actual implementation using SQLAlchemy.

    Design pattern: Dependency Inversion Principle
    - Application layer depends on this interface (abstraction)
    - Infrastructure layer implements this interface (concrete)
    """

    @abstractmethod
    async def create(self, menu_item: MenuItem) -> MenuItem:
        """
        Create a new menu item.

        Args:
            menu_item: MenuItem entity to persist

        Returns:
            MenuItem: Created menu item with DB-generated fields
        """
        ...

    @abstractmethod
    async def get_by_id(self, menu_item_id: UUID) -> MenuItem | None:
        """
        Get menu item by ID.

        Args:
            menu_item_id: Menu item ID

        Returns:
            MenuItem | None: Menu item if found, None otherwise
        """
        ...

    @abstractmethod
    async def get_by_restaurant_id(
        self, restaurant_id: UUID, category: Category | None = None
    ) -> list[MenuItem]:
        """
        Get all menu items for a restaurant.

        Args:
            restaurant_id: Restaurant ID
            category: Optional category filter

        Returns:
            list[MenuItem]: List of menu items
        """
        ...

    @abstractmethod
    async def update(self, menu_item: MenuItem) -> MenuItem:
        """
        Update existing menu item.

        Args:
            menu_item: MenuItem entity with updated fields

        Returns:
            MenuItem: Updated menu item

        Raises:
            MenuItemNotFoundError: If menu item doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, menu_item_id: UUID) -> None:
        """
        Delete menu item (hard delete).

        Note: For soft delete, use MenuItem.discontinue() and update().

        Args:
            menu_item_id: Menu item ID

        Raises:
            MenuItemNotFoundError: If menu item doesn't exist
        """
        ...
