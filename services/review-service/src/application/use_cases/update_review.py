"""Update review use case."""

from src.application.dto.review import ReviewResponseDTO, UpdateReviewDTO
from src.application.interfaces.review_repository import IReviewRepository
from src.domain.exceptions.base import ReviewForbiddenError, ReviewNotFoundError
from src.domain.value_objects.rating import Rating


class UpdateReviewUseCase:
    """Update existing review authored by current user."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, dto: UpdateReviewDTO) -> ReviewResponseDTO:
        """Update review content."""
        review = await self._repository.get_by_id(dto.review_id)
        if review is None:
            raise ReviewNotFoundError(
                "review not found",
                details={"review_id": str(dto.review_id)},
            )
        if review.author_user_id != dto.author_user_id:
            raise ReviewForbiddenError(
                "user cannot update another user's review",
                details={
                    "review_id": str(dto.review_id),
                    "author_user_id": str(dto.author_user_id),
                },
            )

        review.update(
            rating=Rating(dto.rating) if dto.rating is not None else None,
            comment=dto.comment,
        )
        updated = await self._repository.update(review)
        return ReviewResponseDTO.from_entity(updated)
