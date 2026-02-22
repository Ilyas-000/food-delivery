"""
CreateMenuItem Use Case.

Creates a new menu item for a restaurant.
"""

from src.application.dto.menu_item_dto import CreateMenuItemDTO, MenuItemResponseDTO
from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.domain.entities.menu_item import MenuItem
from src.domain.exceptions.restaurant import RestaurantNotFoundError
from src.domain.value_objects.price import Price


class CreateMenuItemUseCase:
    """
    Use case for creating a new menu item.

    Business flow:
    1. Verify restaurant exists
    2. Create Price value object
    3. Create MenuItem entity (validates business rules)
    4. Save to repository
    5. Return DTO
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

    async def execute(self, dto: CreateMenuItemDTO) -> MenuItemResponseDTO:
        """
        Execute use case.

        Args:
            dto: Create menu item data

        Returns:
            MenuItemResponseDTO: Created menu item

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist
            InvalidMenuItemDataError: If validation fails (from Domain)
            ValueError: If price validation fails (from Price VO)
        """
        # 1. Verify restaurant exists
        restaurant = await self._restaurant_repository.get_by_id(dto.restaurant_id)
        if restaurant is None:
            raise RestaurantNotFoundError(str(dto.restaurant_id))

        # 2. Create Price value object
        price = Price(amount=dto.price_amount)

        # 3. Create MenuItem entity (validates business rules)
        menu_item = MenuItem.create(
            restaurant_id=dto.restaurant_id,
            name=dto.name,
            description=dto.description,
            price=price,
            category=dto.category,
            image_url=dto.image_url,
        )

        # 4. Save to repository
        created_menu_item = await self._menu_item_repository.create(menu_item)

        # 5. Return DTO
        return MenuItemResponseDTO.from_entity(created_menu_item)
