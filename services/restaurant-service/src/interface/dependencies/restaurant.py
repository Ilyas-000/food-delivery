"""Restaurant dependencies for FastAPI endpoints."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.menu_item_repository import IMenuItemRepository
from src.application.interfaces.restaurant_repository import IRestaurantRepository
from src.application.use_cases.create_menu_item import CreateMenuItemUseCase
from src.application.use_cases.create_restaurant import CreateRestaurantUseCase
from src.application.use_cases.deactivate_restaurant import DeactivateRestaurantUseCase
from src.application.use_cases.delete_menu_item import DeleteMenuItemUseCase
from src.application.use_cases.get_menu_item import GetMenuItemUseCase
from src.application.use_cases.get_restaurant import GetRestaurantUseCase
from src.application.use_cases.get_restaurant_menu import GetRestaurantMenuUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.application.use_cases.update_menu_item import UpdateMenuItemUseCase
from src.application.use_cases.update_menu_item_availability import (
    UpdateMenuItemAvailabilityUseCase,
)
from src.application.use_cases.update_restaurant import UpdateRestaurantUseCase
from src.interface.dependencies.database import (
    get_menu_item_repository,
    get_restaurant_repository,
)


async def get_create_restaurant_use_case(
    repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> CreateRestaurantUseCase:
    """Provide CreateRestaurantUseCase."""
    return CreateRestaurantUseCase(repository)


async def get_get_restaurant_use_case(
    repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> GetRestaurantUseCase:
    """Provide GetRestaurantUseCase."""
    return GetRestaurantUseCase(repository)


async def get_update_restaurant_use_case(
    repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> UpdateRestaurantUseCase:
    """Provide UpdateRestaurantUseCase."""
    return UpdateRestaurantUseCase(repository)


async def get_deactivate_restaurant_use_case(
    repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> DeactivateRestaurantUseCase:
    """Provide DeactivateRestaurantUseCase."""
    return DeactivateRestaurantUseCase(repository)


async def get_search_restaurants_use_case(
    repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> SearchRestaurantsUseCase:
    """Provide SearchRestaurantsUseCase."""
    return SearchRestaurantsUseCase(repository)


async def get_create_menu_item_use_case(
    menu_item_repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
    restaurant_repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> CreateMenuItemUseCase:
    """Provide CreateMenuItemUseCase."""
    return CreateMenuItemUseCase(menu_item_repository, restaurant_repository)


async def get_get_menu_item_use_case(
    repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
) -> GetMenuItemUseCase:
    """Provide GetMenuItemUseCase."""
    return GetMenuItemUseCase(repository)


async def get_update_menu_item_use_case(
    repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
) -> UpdateMenuItemUseCase:
    """Provide UpdateMenuItemUseCase."""
    return UpdateMenuItemUseCase(repository)


async def get_update_menu_item_availability_use_case(
    repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
) -> UpdateMenuItemAvailabilityUseCase:
    """Provide UpdateMenuItemAvailabilityUseCase."""
    return UpdateMenuItemAvailabilityUseCase(repository)


async def get_delete_menu_item_use_case(
    repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
) -> DeleteMenuItemUseCase:
    """Provide DeleteMenuItemUseCase."""
    return DeleteMenuItemUseCase(repository)


async def get_get_restaurant_menu_use_case(
    menu_item_repository: Annotated[IMenuItemRepository, Depends(get_menu_item_repository)],
    restaurant_repository: Annotated[IRestaurantRepository, Depends(get_restaurant_repository)],
) -> GetRestaurantMenuUseCase:
    """Provide GetRestaurantMenuUseCase."""
    return GetRestaurantMenuUseCase(menu_item_repository, restaurant_repository)
