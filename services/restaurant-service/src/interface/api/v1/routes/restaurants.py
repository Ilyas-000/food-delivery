"""Restaurant routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
import structlog

from src.application.dto.menu_item_dto import (
    CreateMenuItemDTO,
    UpdateMenuItemAvailabilityDTO,
    UpdateMenuItemDTO,
)
from src.application.dto.restaurant_dto import (
    CreateRestaurantDTO,
    SearchRestaurantsDTO,
    UpdateRestaurantDTO,
)
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
from src.domain.value_objects.cuisine import Cuisine
from src.infrastructure.events.publisher import publish_event
from src.interface.api.v1.schemas.menu_item import (
    CreateRestaurantMenuItemRequest,
    MenuItemResponse,
    UpdateMenuItemAvailabilityRequest,
    UpdateMenuItemRequest,
)
from src.interface.api.v1.schemas.restaurant import (
    CreateRestaurantRequest,
    RestaurantResponse,
    UpdateRestaurantRequest,
)
from src.interface.dependencies.restaurant import (
    get_create_menu_item_use_case,
    get_create_restaurant_use_case,
    get_deactivate_restaurant_use_case,
    get_delete_menu_item_use_case,
    get_get_menu_item_use_case,
    get_get_restaurant_menu_use_case,
    get_get_restaurant_use_case,
    get_search_restaurants_use_case,
    get_update_menu_item_availability_use_case,
    get_update_menu_item_use_case,
    get_update_restaurant_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/restaurants",
    tags=["restaurants"],
)


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new restaurant",
)
async def create_restaurant(
    request: CreateRestaurantRequest,
    use_case: Annotated[CreateRestaurantUseCase, Depends(get_create_restaurant_use_case)],
) -> RestaurantResponse:
    """Create a new restaurant."""
    logger.info("restaurants.create.started", owner_id=str(request.owner_id))

    dto = CreateRestaurantDTO(
        owner_id=request.owner_id,
        name=request.name,
        description=request.description,
        street=request.street,
        city=request.city,
        postal_code=request.postal_code,
        latitude=request.latitude,
        longitude=request.longitude,
        cuisine=request.cuisine,
    )
    result_dto = await use_case.execute(dto)
    await publish_event(
        event_type="restaurant.restaurant.created",
        aggregate_type="restaurant",
        aggregate_id=str(result_dto.id),
        user_id=str(result_dto.owner_id),
        payload={
            "owner_id": str(result_dto.owner_id),
            "name": result_dto.name,
            "cuisine": str(result_dto.cuisine),
        },
    )

    logger.info("restaurants.create.success", restaurant_id=str(result_dto.id))
    return RestaurantResponse.from_dto(result_dto)


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get restaurant by ID",
)
async def get_restaurant(
    restaurant_id: UUID,
    use_case: Annotated[GetRestaurantUseCase, Depends(get_get_restaurant_use_case)],
) -> RestaurantResponse:
    """Get restaurant by ID."""
    logger.info("restaurants.get.started", restaurant_id=str(restaurant_id))

    result_dto = await use_case.execute(restaurant_id)

    logger.info("restaurants.get.success", restaurant_id=str(restaurant_id))
    return RestaurantResponse.from_dto(result_dto)


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update restaurant",
)
@router.patch(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_restaurant(
    restaurant_id: UUID,
    request: UpdateRestaurantRequest,
    use_case: Annotated[UpdateRestaurantUseCase, Depends(get_update_restaurant_use_case)],
) -> RestaurantResponse:
    """Update restaurant information."""
    logger.info("restaurants.update.started", restaurant_id=str(restaurant_id))

    dto = UpdateRestaurantDTO(
        name=request.name,
        description=request.description,
        street=request.street,
        city=request.city,
        postal_code=request.postal_code,
        latitude=request.latitude,
        longitude=request.longitude,
        cuisine=request.cuisine,
    )
    result_dto = await use_case.execute(restaurant_id, dto)
    await publish_event(
        event_type="restaurant.restaurant.updated",
        aggregate_type="restaurant",
        aggregate_id=str(result_dto.id),
        user_id=str(result_dto.owner_id),
        payload={
            "name": result_dto.name,
            "description": result_dto.description,
            "cuisine": str(result_dto.cuisine),
            "is_active": result_dto.is_active,
        },
    )

    logger.info("restaurants.update.success", restaurant_id=str(restaurant_id))
    return RestaurantResponse.from_dto(result_dto)


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate restaurant",
)
async def deactivate_restaurant(
    restaurant_id: UUID,
    use_case: Annotated[
        DeactivateRestaurantUseCase,
        Depends(get_deactivate_restaurant_use_case),
    ],
) -> Response:
    """Deactivate restaurant (soft delete)."""
    logger.info("restaurants.deactivate.started", restaurant_id=str(restaurant_id))

    await use_case.execute(restaurant_id)
    await publish_event(
        event_type="restaurant.restaurant.deactivated",
        aggregate_type="restaurant",
        aggregate_id=str(restaurant_id),
        payload={},
    )

    logger.info("restaurants.deactivate.success", restaurant_id=str(restaurant_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=list[RestaurantResponse],
    status_code=status.HTTP_200_OK,
    summary="Search restaurants",
)
async def search_restaurants(
    use_case: Annotated[SearchRestaurantsUseCase, Depends(get_search_restaurants_use_case)],
    cuisine: Cuisine | None = None,
    city: str | None = None,
    min_rating: float | None = None,
    is_active: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> list[RestaurantResponse]:
    """Search restaurants with filters."""
    logger.info(
        "restaurants.search.started",
        cuisine=cuisine,
        city=city,
        min_rating=min_rating,
    )

    dto = SearchRestaurantsDTO(
        cuisine=cuisine,
        city=city,
        min_rating=min_rating,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    result_dtos = await use_case.execute(dto)

    logger.info("restaurants.search.success", count=len(result_dtos))
    return [RestaurantResponse.from_dto(dto) for dto in result_dtos]


@router.get(
    "/{restaurant_id}/menu",
    response_model=list[MenuItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get restaurant menu",
)
async def get_restaurant_menu(
    restaurant_id: UUID,
    use_case: Annotated[
        GetRestaurantMenuUseCase,
        Depends(get_get_restaurant_menu_use_case),
    ],
) -> list[MenuItemResponse]:
    """Get all menu items for a restaurant."""
    logger.info("restaurants.menu.get.started", restaurant_id=str(restaurant_id))

    result_dtos = await use_case.execute(restaurant_id)

    logger.info("restaurants.menu.get.success", count=len(result_dtos))
    return [MenuItemResponse.from_dto(dto) for dto in result_dtos]


@router.get(
    "/{restaurant_id}/menu-items/{menu_item_id}",
    response_model=MenuItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get menu item",
)
async def get_restaurant_menu_item(
    restaurant_id: UUID,
    menu_item_id: UUID,
    use_case: Annotated[GetMenuItemUseCase, Depends(get_get_menu_item_use_case)],
) -> MenuItemResponse:
    """Get a menu item by restaurant and item id."""
    logger.info(
        "restaurants.menu_items.get.started",
        restaurant_id=str(restaurant_id),
        menu_item_id=str(menu_item_id),
    )

    result_dto = await use_case.execute(menu_item_id=menu_item_id, restaurant_id=restaurant_id)

    logger.info("restaurants.menu_items.get.success", menu_item_id=str(result_dto.id))
    return MenuItemResponse.from_dto(result_dto)


@router.post(
    "/{restaurant_id}/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add menu item",
)
async def create_restaurant_menu_item(
    restaurant_id: UUID,
    request: CreateRestaurantMenuItemRequest,
    use_case: Annotated[CreateMenuItemUseCase, Depends(get_create_menu_item_use_case)],
) -> MenuItemResponse:
    """Create menu item inside restaurant."""
    logger.info("restaurants.menu_items.create.started", restaurant_id=str(restaurant_id))

    dto = CreateMenuItemDTO(
        restaurant_id=restaurant_id,
        name=request.name,
        description=request.description,
        price_amount=request.price_amount,
        category=request.category,
        image_url=request.image_url,
    )
    result_dto = await use_case.execute(dto)
    await publish_event(
        event_type="restaurant.menu_item.created",
        aggregate_type="menu_item",
        aggregate_id=str(result_dto.id),
        payload={
            "restaurant_id": str(result_dto.restaurant_id),
            "name": result_dto.name,
            "category": str(result_dto.category),
            "availability": str(result_dto.availability),
        },
    )

    logger.info("restaurants.menu_items.create.success", menu_item_id=str(result_dto.id))
    return MenuItemResponse.from_dto(result_dto)


@router.put(
    "/{restaurant_id}/menu-items/{menu_item_id}",
    response_model=MenuItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update menu item",
)
async def update_restaurant_menu_item(
    restaurant_id: UUID,
    menu_item_id: UUID,
    request: UpdateMenuItemRequest,
    use_case: Annotated[UpdateMenuItemUseCase, Depends(get_update_menu_item_use_case)],
) -> MenuItemResponse:
    """Update menu item in restaurant."""
    logger.info(
        "restaurants.menu_items.update.started",
        restaurant_id=str(restaurant_id),
        menu_item_id=str(menu_item_id),
    )

    dto = UpdateMenuItemDTO(
        name=request.name,
        description=request.description,
        price_amount=request.price_amount,
        category=request.category,
        image_url=request.image_url,
    )
    result_dto = await use_case.execute(
        menu_item_id=menu_item_id,
        dto=dto,
        restaurant_id=restaurant_id,
    )
    await publish_event(
        event_type="restaurant.menu_item.updated",
        aggregate_type="menu_item",
        aggregate_id=str(result_dto.id),
        payload={
            "restaurant_id": str(result_dto.restaurant_id),
            "name": result_dto.name,
            "category": str(result_dto.category),
            "availability": str(result_dto.availability),
        },
    )

    logger.info("restaurants.menu_items.update.success", menu_item_id=str(result_dto.id))
    return MenuItemResponse.from_dto(result_dto)


@router.patch(
    "/{restaurant_id}/menu-items/{menu_item_id}/availability",
    response_model=MenuItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update menu item availability",
)
async def update_restaurant_menu_item_availability(
    restaurant_id: UUID,
    menu_item_id: UUID,
    request: UpdateMenuItemAvailabilityRequest,
    use_case: Annotated[
        UpdateMenuItemAvailabilityUseCase,
        Depends(get_update_menu_item_availability_use_case),
    ],
) -> MenuItemResponse:
    """Update menu item availability."""
    logger.info(
        "restaurants.menu_items.availability.started",
        restaurant_id=str(restaurant_id),
        menu_item_id=str(menu_item_id),
        availability=request.availability,
    )

    dto = UpdateMenuItemAvailabilityDTO(availability=request.availability)
    result_dto = await use_case.execute(restaurant_id, menu_item_id, dto)
    await publish_event(
        event_type="restaurant.menu_item.availability_changed",
        aggregate_type="menu_item",
        aggregate_id=str(result_dto.id),
        payload={
            "restaurant_id": str(result_dto.restaurant_id),
            "availability": str(result_dto.availability),
        },
    )

    logger.info(
        "restaurants.menu_items.availability.success",
        menu_item_id=str(result_dto.id),
        availability=result_dto.availability,
    )
    return MenuItemResponse.from_dto(result_dto)


@router.delete(
    "/{restaurant_id}/menu-items/{menu_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete menu item",
)
async def delete_restaurant_menu_item(
    restaurant_id: UUID,
    menu_item_id: UUID,
    use_case: Annotated[DeleteMenuItemUseCase, Depends(get_delete_menu_item_use_case)],
) -> Response:
    """Delete menu item from restaurant (soft delete)."""
    logger.info(
        "restaurants.menu_items.delete.started",
        restaurant_id=str(restaurant_id),
        menu_item_id=str(menu_item_id),
    )

    await use_case.execute(restaurant_id, menu_item_id)
    await publish_event(
        event_type="restaurant.menu_item.deleted",
        aggregate_type="menu_item",
        aggregate_id=str(menu_item_id),
        payload={"restaurant_id": str(restaurant_id)},
    )

    logger.info("restaurants.menu_items.delete.success", menu_item_id=str(menu_item_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
