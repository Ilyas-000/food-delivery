"""Get review use case."""

from uuid import UUID

from src.application.dto.review import ReviewResponseDTO
from src.application.interfaces.review_repository import IReviewRepository
from src.domain.exceptions.base import ReviewNotFoundError


class GetReviewUseCase:
    """Fetch review by id."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, review_id: UUID) -> ReviewResponseDTO:
        """Return review DTO."""
        review = await self._repository.get_by_id(review_id)
        if review is None:
            raise ReviewNotFoundError("review not found", details={"review_id": str(review_id)})
        return ReviewResponseDTO.from_entity(review)
