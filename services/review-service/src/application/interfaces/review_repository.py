"""Review repository contract."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto.review import CourierRatingDTO, RestaurantRatingDTO
from src.domain.entities.review import Review
from src.domain.value_objects.review_target import ReviewTargetType


class IReviewRepository(ABC):
    """Persistence contract for reviews."""

    @abstractmethod
    async def create(self, review: Review) -> Review:
        """Create review."""

    @abstractmethod
    async def get_by_id(self, review_id: UUID) -> Review | None:
        """Get review by id."""

    @abstractmethod
    async def get_by_order_author_and_target(
        self,
        order_id: UUID,
        author_user_id: UUID,
        target_type: ReviewTargetType,
    ) -> Review | None:
        """Get review by order, author, and target type."""

    @abstractmethod
    async def list_reviews(
        self,
        *,
        restaurant_id: UUID | None,
        courier_id: UUID | None,
        author_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Review], int]:
        """List reviews with filters."""

    @abstractmethod
    async def update(self, review: Review) -> Review:
        """Update review."""

    @abstractmethod
    async def delete(self, review_id: UUID) -> None:
        """Delete review."""

    @abstractmethod
    async def get_restaurant_rating(self, restaurant_id: UUID) -> RestaurantRatingDTO:
        """Get aggregated rating summary."""

    @abstractmethod
    async def get_courier_rating(self, courier_id: UUID) -> CourierRatingDTO:
        """Get aggregated courier rating summary."""
