"""
GetMenuItem Use Case.

Retrieves a menu item by ID.
"""

from uuid import UUID

from src.application.dto import MenuItemResponseDTO
from src.application.interfaces import IMenuItemRepository
from src.domain.exceptions import MenuItemNotFoundError


class GetMenuItemUseCase:
    """
    Use case for retrieving a menu item by ID.

    Business flow:
    1. Fetch menu item from repository
    2. If not found, raise exception
    3. Return DTO
    """

    def __init__(self, menu_item_repository: IMenuItemRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            menu_item_repository: Menu item repository interface
        """
        self._menu_item_repository = menu_item_repository

    async def execute(self, menu_item_id: UUID) -> MenuItemResponseDTO:
        """
        Execute use case.

        Args:
            menu_item_id: ID of the menu item to retrieve

        Returns:
            MenuItemResponseDTO: Menu item data

        Raises:
            MenuItemNotFoundError: If menu item doesn't exist
        """
        menu_item = await self._menu_item_repository.get_by_id(menu_item_id)

        if menu_item is None:
            raise MenuItemNotFoundError(str(menu_item_id))

        return MenuItemResponseDTO.from_entity(menu_item)
