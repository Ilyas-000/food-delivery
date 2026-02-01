"""Restaurant routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
import structlog

from src.application.dto.restaurant_dto import (
    CreateRestaurantDTO,
    SearchRestaurantsDTO,
    UpdateRestaurantDTO,
)
from src.application.use_cases.create_restaurant import CreateRestaurantUseCase
from src.application.use_cases.get_restaurant import GetRestaurantUseCase
from src.application.use_cases.search_restaurants import SearchRestaurantsUseCase
from src.application.use_cases.update_restaurant import UpdateRestaurantUseCase
from src.domain.value_objects.cuisine import Cuisine
from src.interface.api.v1.schemas.restaurant import (
    CreateRestaurantRequest,
    RestaurantResponse,
    UpdateRestaurantRequest,
)
from src.interface.dependencies.restaurant import (
    get_create_restaurant_use_case,
    get_get_restaurant_use_case,
    get_search_restaurants_use_case,
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


@router.patch(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update restaurant",
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

    logger.info("restaurants.update.success", restaurant_id=str(restaurant_id))
    return RestaurantResponse.from_dto(result_dto)


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
