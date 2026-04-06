"""Delete review use case."""

from uuid import UUID

from src.application.interfaces.review_repository import IReviewRepository
from src.domain.exceptions.base import ReviewForbiddenError, ReviewNotFoundError


class DeleteReviewUseCase:
    """Delete review authored by current user."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, review_id: UUID, author_user_id: UUID) -> None:
        """Delete review if user owns it."""
        review = await self._repository.get_by_id(review_id)
        if review is None:
            raise ReviewNotFoundError("review not found", details={"review_id": str(review_id)})
        if review.author_user_id != author_user_id:
            raise ReviewForbiddenError(
                "user cannot delete another user's review",
                details={"review_id": str(review_id), "author_user_id": str(author_user_id)},
            )
        await self._repository.delete(review_id)
