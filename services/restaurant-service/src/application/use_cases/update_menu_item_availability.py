"""UpdateMenuItemAvailability use case."""

from uuid import UUID

from src.application.dto.menu_item_dto import MenuItemResponseDTO, UpdateMenuItemAvailabilityDTO
from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.domain.exceptions.menu_item import MenuItemNotFoundError, MenuItemNotInRestaurantError
from src.domain.value_objects.availability import Availability


class UpdateMenuItemAvailabilityUseCase:
    """Update menu item availability state."""

    def __init__(self, menu_item_repository: IMenuItemRepository) -> None:
        self._menu_item_repository = menu_item_repository

    async def execute(
        self,
        restaurant_id: UUID,
        menu_item_id: UUID,
        dto: UpdateMenuItemAvailabilityDTO,
    ) -> MenuItemResponseDTO:
        menu_item = await self._menu_item_repository.get_by_id(menu_item_id)
        if menu_item is None:
            raise MenuItemNotFoundError(str(menu_item_id))

        if menu_item.restaurant_id != restaurant_id:
            raise MenuItemNotInRestaurantError(str(menu_item_id), str(restaurant_id))

        if dto.availability == Availability.AVAILABLE:
            menu_item.mark_available()
        elif dto.availability == Availability.OUT_OF_STOCK:
            menu_item.mark_unavailable()
        else:
            menu_item.discontinue()

        updated_menu_item = await self._menu_item_repository.update(menu_item)
        return MenuItemResponseDTO.from_entity(updated_menu_item)
