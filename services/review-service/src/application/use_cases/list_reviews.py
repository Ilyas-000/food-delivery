"""List reviews use case."""

from src.application.dto.review import ListReviewsDTO, ReviewListResponseDTO, ReviewResponseDTO
from src.application.interfaces.review_repository import IReviewRepository


class ListReviewsUseCase:
    """List reviews with optional filters."""

    def __init__(self, repository: IReviewRepository) -> None:
        self._repository = repository

    async def execute(self, dto: ListReviewsDTO) -> ReviewListResponseDTO:
        """Return paginated review list."""
        reviews, total = await self._repository.list_reviews(
            restaurant_id=dto.restaurant_id,
            courier_id=dto.courier_id,
            author_user_id=dto.author_user_id,
            limit=dto.limit,
            offset=dto.offset,
        )
        return ReviewListResponseDTO(
            items=[ReviewResponseDTO.from_entity(review) for review in reviews],
            total=total,
            limit=dto.limit,
            offset=dto.offset,
        )
