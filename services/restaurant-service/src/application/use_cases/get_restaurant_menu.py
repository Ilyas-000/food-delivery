"""
GetRestaurantMenu Use Case.

Retrieves all menu items for a restaurant.
"""

from uuid import UUID

from src.application.dto import MenuItemResponseDTO
from src.application.interfaces import IMenuItemRepository, IRestaurantRepository
from src.domain.exceptions import RestaurantNotFoundError


class GetRestaurantMenuUseCase:
    """
    Use case for retrieving all menu items for a restaurant.

    Business flow:
    1. Verify restaurant exists
    2. Fetch menu items from repository
    3. Convert entities to DTOs
    4. Return list of DTOs
    """

    def __init__(
        self,
        menu_item_repository: IMenuItemRepository,
        restaurant_repository: IRestaurantRepository,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            menu_item_repository: Menu item repository interface
            restaurant_repository: Restaurant repository interface
        """
        self._menu_item_repository = menu_item_repository
        self._restaurant_repository = restaurant_repository

    async def execute(self, restaurant_id: UUID) -> list[MenuItemResponseDTO]:
        """
        Execute use case.

        Args:
            restaurant_id: ID of the restaurant

        Returns:
            list[MenuItemResponseDTO]: List of menu items

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
        """
        # 1. Verify restaurant exists
        restaurant = await self._restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise RestaurantNotFoundError(str(restaurant_id))

        # 2. Fetch menu items
        menu_items = await self._menu_item_repository.get_by_restaurant_id(restaurant_id)

        # 3. Convert to DTOs
        return [MenuItemResponseDTO.from_entity(item) for item in menu_items]
