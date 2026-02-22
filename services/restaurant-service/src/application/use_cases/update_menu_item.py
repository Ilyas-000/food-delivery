"""
UpdateMenuItem Use Case.

Updates menu item information.
"""

from uuid import UUID

from src.application.dto.menu_item_dto import MenuItemResponseDTO, UpdateMenuItemDTO
from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.domain.exceptions.menu_item import MenuItemNotFoundError, MenuItemNotInRestaurantError
from src.domain.value_objects.price import Price


class UpdateMenuItemUseCase:
    """
    Use case for updating menu item information.

    Business flow:
    1. Fetch menu item from repository
    2. If not found, raise exception
    3. Create new Price if price_amount provided
    4. Update menu item entity (validates business rules)
    5. Save to repository
    6. Return DTO
    """

    def __init__(self, menu_item_repository: IMenuItemRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            menu_item_repository: Menu item repository interface
        """
        self._menu_item_repository = menu_item_repository

    async def execute(
        self,
        menu_item_id: UUID,
        dto: UpdateMenuItemDTO,
        restaurant_id: UUID | None = None,
    ) -> MenuItemResponseDTO:
        """
        Execute use case.

        Args:
            menu_item_id: ID of the menu item to update
            dto: Update data
            restaurant_id: Optional restaurant scope check

        Returns:
            MenuItemResponseDTO: Updated menu item

        Raises:
            MenuItemNotFoundError: If menu item doesn't exist
            InvalidMenuItemDataError: If validation fails (from Domain)
            ValueError: If price validation fails (from Price VO)
        """
        # 1. Fetch menu item
        menu_item = await self._menu_item_repository.get_by_id(menu_item_id)

        if menu_item is None:
            raise MenuItemNotFoundError(str(menu_item_id))

        if restaurant_id is not None and menu_item.restaurant_id != restaurant_id:
            raise MenuItemNotInRestaurantError(str(menu_item_id), str(restaurant_id))

        # 2. Create new Price if price_amount is provided
        new_price = None
        if dto.price_amount is not None:
            new_price = Price(amount=dto.price_amount)

        # 3. Update menu item entity (validates business rules)
        menu_item.update_info(
            name=dto.name,
            description=dto.description,
            price=new_price,
            category=dto.category,
            image_url=dto.image_url,
        )

        # 4. Save to repository
        updated_menu_item = await self._menu_item_repository.update(menu_item)

        # 5. Return DTO
        return MenuItemResponseDTO.from_entity(updated_menu_item)
