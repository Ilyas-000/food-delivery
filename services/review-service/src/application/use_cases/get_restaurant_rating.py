"""Restaurant rating summary use case."""

from uuid import UUID

from src.application.dto.review import RestaurantRatingDTO
from src.application.interfaces.review_repository import IReviewRepository


class GetRestaurantRatingUseCase:
    """Compute current rating summary for a restaurant."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, restaurant_id: UUID) -> RestaurantRatingDTO:
        """Return restaurant rating summary."""
        return await self._repository.get_restaurant_rating(restaurant_id)
