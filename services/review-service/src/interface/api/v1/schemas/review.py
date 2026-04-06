"""API schemas for review-service."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.application.dto.review import (
    CourierRatingDTO,
    RestaurantRatingDTO,
    ReviewListResponseDTO,
    ReviewResponseDTO,
)
from src.domain.value_objects.review_target import ReviewTargetType


class CreateReviewRequest(BaseModel):
    """Create review request schema."""

    order_id: UUID
    target_type: ReviewTargetType
    target_id: UUID
    rating: Annotated[int, Field(ge=1, le=5)]
    comment: Annotated[str | None, Field(max_length=1000)] = None


class UpdateReviewRequest(BaseModel):
    """Update review request schema."""

    rating: Annotated[int | None, Field(ge=1, le=5)] = None
    comment: Annotated[str | None, Field(max_length=1000)] = None

    @model_validator(mode="after")
    def ensure_has_payload(self) -> "UpdateReviewRequest":
        """Require at least one mutable field."""
        if self.rating is None and self.comment is None:
            raise ValueError("at least one field must be provided")
        return self


class ReviewResponse(BaseModel):
    """Review response schema."""

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
    def from_dto(cls, dto: ReviewResponseDTO) -> "ReviewResponse":
        """Build API schema from DTO."""
        return cls(**dto.model_dump())


class ReviewListResponse(BaseModel):
    """Paginated review list response."""

    items: list[ReviewResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_dto(cls, dto: ReviewListResponseDTO) -> "ReviewListResponse":
        """Build API schema from DTO."""
        return cls(
            items=[ReviewResponse.from_dto(item) for item in dto.items],
            total=dto.total,
            limit=dto.limit,
            offset=dto.offset,
        )


class RestaurantRatingResponse(BaseModel):
    """Restaurant rating summary response."""

    restaurant_id: UUID
    average_rating: Decimal
    reviews_count: int

    @classmethod
    def from_dto(cls, dto: RestaurantRatingDTO) -> "RestaurantRatingResponse":
        """Build API schema from DTO."""
        return cls(**dto.model_dump())


class CourierRatingResponse(BaseModel):
    """Courier rating summary response."""

    courier_id: UUID
    average_rating: Decimal
    reviews_count: int

    @classmethod
    def from_dto(cls, dto: CourierRatingDTO) -> "CourierRatingResponse":
        """Build API schema from DTO."""
        return cls(**dto.model_dump())
