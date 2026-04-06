"""Review DTOs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.review import Review
from src.domain.value_objects.review_target import ReviewTargetType


class OrderSnapshotDTO(BaseModel):
    """Minimal order data required for review validation."""

    order_id: UUID
    user_id: UUID
    restaurant_id: UUID
    status: str


class DeliverySnapshotDTO(BaseModel):
    """Minimal delivery data required for review validation."""

    assignment_id: UUID
    order_id: UUID
    restaurant_id: UUID
    courier_id: UUID
    status: str
    delivered_at: datetime | None


class CreateReviewDTO(BaseModel):
    """Input payload for review creation."""

    order_id: UUID
    author_user_id: UUID
    target_type: ReviewTargetType
    target_id: UUID
    rating: int
    comment: str | None = None


class UpdateReviewDTO(BaseModel):
    """Input payload for review update."""

    review_id: UUID
    author_user_id: UUID
    rating: int | None = None
    comment: str | None = None


class ListReviewsDTO(BaseModel):
    """Review list filters."""

    restaurant_id: UUID | None = None
    courier_id: UUID | None = None
    author_user_id: UUID | None = None
    limit: int = 20
    offset: int = 0


class ReviewResponseDTO(BaseModel):
    """Serialized review payload."""

    id: UUID
    order_id: UUID
    author_user_id: UUID
    target_type: ReviewTargetType
    target_id: UUID
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, review: Review) -> "ReviewResponseDTO":
        """Build DTO from entity."""
        return cls(
            id=review.id,
            order_id=review.order_id,
            author_user_id=review.author_user_id,
            target_type=review.target_type,
            target_id=review.target_id,
            rating=review.rating.value,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )


class ReviewListResponseDTO(BaseModel):
    """Paginated list of reviews."""

    items: list[ReviewResponseDTO]
    total: int
    limit: int
    offset: int


class RestaurantRatingDTO(BaseModel):
    """Restaurant rating summary."""

    restaurant_id: UUID
    average_rating: Decimal
    reviews_count: int


class CourierRatingDTO(BaseModel):
    """Courier rating summary."""

    courier_id: UUID
    average_rating: Decimal
    reviews_count: int
