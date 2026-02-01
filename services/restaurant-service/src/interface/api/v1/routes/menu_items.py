"""Menu item routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
import structlog

from src.application.dto.menu_item_dto import CreateMenuItemDTO, UpdateMenuItemDTO
from src.application.use_cases.create_menu_item import CreateMenuItemUseCase
from src.application.use_cases.get_menu_item import GetMenuItemUseCase
from src.application.use_cases.get_restaurant_menu import GetRestaurantMenuUseCase
from src.application.use_cases.update_menu_item import UpdateMenuItemUseCase
from src.interface.api.v1.schemas.menu_item import (
    CreateMenuItemRequest,
    MenuItemResponse,
    UpdateMenuItemRequest,
)
from src.interface.dependencies.restaurant import (
    get_create_menu_item_use_case,
    get_get_menu_item_use_case,
    get_get_restaurant_menu_use_case,
    get_update_menu_item_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/menu-items",
    tags=["menu-items"],
)


@router.post(
    "",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new menu item",
)
async def create_menu_item(
    request: CreateMenuItemRequest,
    use_case: Annotated[CreateMenuItemUseCase, Depends(get_create_menu_item_use_case)],
) -> MenuItemResponse:
    """Create a new menu item."""
    logger.info(
        "menu_items.create.started",
        restaurant_id=str(request.restaurant_id),
    )

    dto = CreateMenuItemDTO(
        restaurant_id=request.restaurant_id,
        name=request.name,
        description=request.description,
        price_amount=request.price_amount,
        category=request.category,
        image_url=request.image_url,
    )
    result_dto = await use_case.execute(dto)

    logger.info("menu_items.create.success", menu_item_id=str(result_dto.id))
    return MenuItemResponse.from_dto(result_dto)


@router.get(
    "/{menu_item_id}",
    response_model=MenuItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get menu item by ID",
)
async def get_menu_item(
    menu_item_id: UUID,
    use_case: Annotated[GetMenuItemUseCase, Depends(get_get_menu_item_use_case)],
) -> MenuItemResponse:
    """Get menu item by ID."""
    logger.info("menu_items.get.started", menu_item_id=str(menu_item_id))

    result_dto = await use_case.execute(menu_item_id)

    logger.info("menu_items.get.success", menu_item_id=str(menu_item_id))
    return MenuItemResponse.from_dto(result_dto)


@router.patch(
    "/{menu_item_id}",
    response_model=MenuItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update menu item",
)
async def update_menu_item(
    menu_item_id: UUID,
    request: UpdateMenuItemRequest,
    use_case: Annotated[UpdateMenuItemUseCase, Depends(get_update_menu_item_use_case)],
) -> MenuItemResponse:
    """Update menu item information."""
    logger.info("menu_items.update.started", menu_item_id=str(menu_item_id))

    dto = UpdateMenuItemDTO(
        name=request.name,
        description=request.description,
        price_amount=request.price_amount,
        category=request.category,
        image_url=request.image_url,
    )
    result_dto = await use_case.execute(menu_item_id, dto)

    logger.info("menu_items.update.success", menu_item_id=str(menu_item_id))
    return MenuItemResponse.from_dto(result_dto)


@router.get(
    "/restaurant/{restaurant_id}",
    response_model=list[MenuItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all menu items for a restaurant",
)
async def get_restaurant_menu(
    restaurant_id: UUID,
    use_case: Annotated[GetRestaurantMenuUseCase, Depends(get_get_restaurant_menu_use_case)],
) -> list[MenuItemResponse]:
    """Get all menu items for a restaurant."""
    logger.info("menu_items.restaurant.get.started", restaurant_id=str(restaurant_id))

    result_dtos = await use_case.execute(restaurant_id)

    logger.info("menu_items.restaurant.get.success", count=len(result_dtos))
    return [MenuItemResponse.from_dto(dto) for dto in result_dtos]
