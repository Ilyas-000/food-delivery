"""DeleteMenuItem use case."""

from uuid import UUID

from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.domain.exceptions.menu_item import MenuItemNotFoundError, MenuItemNotInRestaurantError


class DeleteMenuItemUseCase:
    """Soft-delete menu item by marking it as discontinued."""

    def __init__(self, menu_item_repository: IMenuItemRepository) -> None:
        self._menu_item_repository = menu_item_repository

    async def execute(self, restaurant_id: UUID, menu_item_id: UUID) -> None:
        menu_item = await self._menu_item_repository.get_by_id(menu_item_id)
        if menu_item is None:
            raise MenuItemNotFoundError(str(menu_item_id))

        if menu_item.restaurant_id != restaurant_id:
            raise MenuItemNotInRestaurantError(str(menu_item_id), str(restaurant_id))

        menu_item.discontinue()
        await self._menu_item_repository.update(menu_item)
