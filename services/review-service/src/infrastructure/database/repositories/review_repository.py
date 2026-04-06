"""SQLAlchemy repository for review persistence."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.application.dto.review import CourierRatingDTO, RestaurantRatingDTO
from src.application.interfaces.review_repository import IReviewRepository
from src.domain.entities.review import Review
from src.domain.exceptions.base import ReviewAlreadyExistsError
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.review_target import ReviewTargetType
from src.infrastructure.database.models.review_model import ReviewModel

logger = structlog.get_logger(__name__)


class ReviewRepository(IReviewRepository):
    """Persist and query reviews through SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, review: Review) -> Review:
        """Create review record."""
        model = self._entity_to_model(review)
        try:
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return self._model_to_entity(model)
        except IntegrityError as exc:
            await self._session.rollback()
            logger.exception("repository.create_review.integrity_error", error=str(exc))
            raise ReviewAlreadyExistsError(
                "review for this order already exists",
                details={
                    "order_id": str(review.order_id),
                    "author_user_id": str(review.author_user_id),
                    "target_type": review.target_type.value,
                },
            ) from exc

    async def get_by_id(self, review_id: UUID) -> Review | None:
        """Get review by id."""
        model = await self._session.get(ReviewModel, review_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_order_author_and_target(
        self,
        order_id: UUID,
        author_user_id: UUID,
        target_type: ReviewTargetType,
    ) -> Review | None:
        """Get review by order, author, and target type."""
        stmt = select(ReviewModel).where(
            ReviewModel.order_id == order_id,
            ReviewModel.author_user_id == author_user_id,
            ReviewModel.target_type == target_type.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_reviews(
        self,
        *,
        restaurant_id: UUID | None,
        courier_id: UUID | None,
        author_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Review], int]:
        """List reviews with total count."""
        stmt = select(ReviewModel)
        count_stmt = select(func.count(ReviewModel.id))

        if restaurant_id is not None:
            stmt = stmt.where(
                ReviewModel.target_type == ReviewTargetType.RESTAURANT.value,
                ReviewModel.target_id == restaurant_id,
            )
            count_stmt = count_stmt.where(
                ReviewModel.target_type == ReviewTargetType.RESTAURANT.value,
                ReviewModel.target_id == restaurant_id,
            )
        if courier_id is not None:
            stmt = stmt.where(
                ReviewModel.target_type == ReviewTargetType.COURIER.value,
                ReviewModel.target_id == courier_id,
            )
            count_stmt = count_stmt.where(
                ReviewModel.target_type == ReviewTargetType.COURIER.value,
                ReviewModel.target_id == courier_id,
            )
        if author_user_id is not None:
            stmt = stmt.where(ReviewModel.author_user_id == author_user_id)
            count_stmt = count_stmt.where(ReviewModel.author_user_id == author_user_id)

        stmt = stmt.order_by(ReviewModel.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)

        models = result.scalars().all()
        total = count_result.scalar_one()
        return [self._model_to_entity(model) for model in models], int(total)

    async def update(self, review: Review) -> Review:
        """Update persisted review."""
        model = await self._session.get(ReviewModel, review.id)
        if model is None:
            raise ValueError(f"review '{review.id}' not found")

        model.rating = review.rating.value
        model.comment = review.comment
        model.updated_at = review.updated_at
        await self._session.commit()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def delete(self, review_id: UUID) -> None:
        """Delete review by id."""
        model = await self._session.get(ReviewModel, review_id)
        if model is None:
            return
        await self._session.delete(model)
        await self._session.commit()

    async def get_restaurant_rating(self, restaurant_id: UUID) -> RestaurantRatingDTO:
        """Return average rating and count for restaurant."""
        stmt = select(
            func.avg(ReviewModel.rating),
            func.count(ReviewModel.id),
        ).where(
            ReviewModel.target_type == ReviewTargetType.RESTAURANT.value,
            ReviewModel.target_id == restaurant_id,
        )
        result = await self._session.execute(stmt)
        average, count = result.one()
        average_rating = Decimal(str(average or "0")).quantize(Decimal("0.01"))
        return RestaurantRatingDTO(
            restaurant_id=restaurant_id,
            average_rating=average_rating,
            reviews_count=int(count or 0),
        )

    async def get_courier_rating(self, courier_id: UUID) -> CourierRatingDTO:
        """Return average rating and count for courier."""
        stmt = select(
            func.avg(ReviewModel.rating),
            func.count(ReviewModel.id),
        ).where(
            ReviewModel.target_type == ReviewTargetType.COURIER.value,
            ReviewModel.target_id == courier_id,
        )
        result = await self._session.execute(stmt)
        average, count = result.one()
        average_rating = Decimal(str(average or "0")).quantize(Decimal("0.01"))
        return CourierRatingDTO(
            courier_id=courier_id,
            average_rating=average_rating,
            reviews_count=int(count or 0),
        )

    @staticmethod
    def _entity_to_model(review: Review) -> ReviewModel:
        """Convert entity to ORM model."""
        return ReviewModel(
            id=review.id,
            order_id=review.order_id,
            author_user_id=review.author_user_id,
            target_type=review.target_type.value,
            target_id=review.target_id,
            rating=review.rating.value,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    @staticmethod
    def _model_to_entity(model: ReviewModel) -> Review:
        """Convert ORM model to entity."""
        return Review(
            id=model.id,
            order_id=model.order_id,
            author_user_id=model.author_user_id,
            target_type=ReviewTargetType(model.target_type),
            target_id=model.target_id,
            rating=Rating(model.rating),
            comment=model.comment,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
