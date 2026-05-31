"""Review routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
import structlog

from src.application.dto.review import CreateReviewDTO, ListReviewsDTO, UpdateReviewDTO
from src.application.use_cases.create_review import CreateReviewUseCase
from src.application.use_cases.delete_review import DeleteReviewUseCase
from src.application.use_cases.get_courier_rating import GetCourierRatingUseCase
from src.application.use_cases.get_restaurant_rating import GetRestaurantRatingUseCase
from src.application.use_cases.get_review import GetReviewUseCase
from src.application.use_cases.list_reviews import ListReviewsUseCase
from src.application.use_cases.update_review import UpdateReviewUseCase
from src.infrastructure.events.publisher import publish_event
from src.interface.api.v1.schemas.review import (
    CourierRatingResponse,
    CreateReviewRequest,
    RestaurantRatingResponse,
    ReviewListResponse,
    ReviewResponse,
    UpdateReviewRequest,
)
from src.interface.dependencies.auth import get_current_user_id
from src.interface.dependencies.review import (
    get_courier_rating_use_case,
    get_create_review_use_case,
    get_delete_review_use_case,
    get_get_review_use_case,
    get_list_reviews_use_case,
    get_restaurant_rating_use_case,
    get_update_review_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    http_request: Request,
    request: CreateReviewRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[CreateReviewUseCase, Depends(get_create_review_use_case)],
) -> ReviewResponse:
    """Create review for a delivered order."""
    dto = CreateReviewDTO(
        order_id=request.order_id,
        author_user_id=current_user_id,
        target_type=request.target_type,
        target_id=request.target_id,
        rating=request.rating,
        comment=request.comment,
    )
    result = await use_case.execute(dto)
    await publish_event(
        event_type="review-service.review.created",
        aggregate_type="review",
        aggregate_id=str(result.id),
        user_id=str(result.author_user_id),
        payload={
            "order_id": str(result.order_id),
            "target_type": result.target_type.value,
            "target_id": str(result.target_id),
            "rating": result.rating,
        },
    )
    http_request.app.state.reviews_created_total.labels(
        target_type=result.target_type.value,
        result="success",
    ).inc()
    logger.info("reviews.create.success", review_id=str(result.id), order_id=str(result.order_id))
    return ReviewResponse.from_dto(result)


@router.get("", response_model=ReviewListResponse, status_code=status.HTTP_200_OK)
async def list_reviews(
    use_case: Annotated[ListReviewsUseCase, Depends(get_list_reviews_use_case)],
    restaurant_id: UUID | None = None,
    courier_id: UUID | None = None,
    author_user_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ReviewListResponse:
    """List reviews using optional restaurant or author filters."""
    dto = ListReviewsDTO(
        restaurant_id=restaurant_id,
        courier_id=courier_id,
        author_user_id=author_user_id,
        limit=limit,
        offset=offset,
    )
    result = await use_case.execute(dto)
    return ReviewListResponse.from_dto(result)


@router.get("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def get_review(
    review_id: UUID,
    use_case: Annotated[GetReviewUseCase, Depends(get_get_review_use_case)],
) -> ReviewResponse:
    """Get single review by id."""
    result = await use_case.execute(review_id)
    return ReviewResponse.from_dto(result)


@router.patch("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    review_id: UUID,
    request: UpdateReviewRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[UpdateReviewUseCase, Depends(get_update_review_use_case)],
) -> ReviewResponse:
    """Update existing review."""
    dto = UpdateReviewDTO(
        review_id=review_id,
        author_user_id=current_user_id,
        rating=request.rating,
        comment=request.comment,
    )
    result = await use_case.execute(dto)
    return ReviewResponse.from_dto(result)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    use_case: Annotated[DeleteReviewUseCase, Depends(get_delete_review_use_case)],
) -> Response:
    """Delete review authored by current user."""
    await use_case.execute(review_id, current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/restaurants/{restaurant_id}/rating",
    response_model=RestaurantRatingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_restaurant_rating(
    restaurant_id: UUID,
    use_case: Annotated[GetRestaurantRatingUseCase, Depends(get_restaurant_rating_use_case)],
) -> RestaurantRatingResponse:
    """Get restaurant rating summary."""
    result = await use_case.execute(restaurant_id)
    return RestaurantRatingResponse.from_dto(result)


@router.get(
    "/couriers/{courier_id}/rating",
    response_model=CourierRatingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_courier_rating(
    courier_id: UUID,
    use_case: Annotated[GetCourierRatingUseCase, Depends(get_courier_rating_use_case)],
) -> CourierRatingResponse:
    """Get courier rating summary."""
    result = await use_case.execute(courier_id)
    return CourierRatingResponse.from_dto(result)
