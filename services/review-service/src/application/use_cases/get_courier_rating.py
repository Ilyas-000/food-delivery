"""Courier rating summary use case."""

from uuid import UUID

from src.application.dto.review import CourierRatingDTO
from src.application.interfaces.review_repository import IReviewRepository


class GetCourierRatingUseCase:
    """Compute current rating summary for a courier."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, courier_id: UUID) -> CourierRatingDTO:
        """Return courier rating summary."""
        return await self._repository.get_courier_rating(courier_id)
