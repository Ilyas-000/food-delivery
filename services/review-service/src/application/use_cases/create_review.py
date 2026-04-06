"""Create review use case."""

from src.application.dto.review import CreateReviewDTO, ReviewResponseDTO
from src.application.interfaces.review_repository import IReviewRepository
from src.application.interfaces.validation_clients import (
    IDeliveryValidationClient,
    IOrderValidationClient,
)
from src.domain.entities.review import Review
from src.domain.exceptions.base import (
    InvalidReviewDataError,
    ReviewAlreadyExistsError,
    ReviewForbiddenError,
)
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.review_target import ReviewTargetType


class CreateReviewUseCase:
    """Create a restaurant review for a delivered order."""

    def __init__(
        self,
        repository: IReviewRepository,
        order_client: IOrderValidationClient,
        delivery_client: IDeliveryValidationClient,
    ) -> None:
        self._repository = repository
        self._order_client = order_client
        self._delivery_client = delivery_client

    async def execute(self, dto: CreateReviewDTO) -> ReviewResponseDTO:
        """Validate upstream state and create review."""
        existing = await self._repository.get_by_order_author_and_target(
            dto.order_id,
            dto.author_user_id,
            dto.target_type,
        )
        if existing is not None:
            raise ReviewAlreadyExistsError(
                "review for this order and target already exists",
                details={
                    "order_id": str(dto.order_id),
                    "author_user_id": str(dto.author_user_id),
                    "target_type": dto.target_type.value,
                },
            )

        try:
            order = await self._order_client.get_order(dto.order_id)
            delivery = await self._delivery_client.get_delivery(dto.order_id)
        except LookupError as exc:
            raise InvalidReviewDataError("order must exist and be delivered before review") from exc

        if order.user_id != dto.author_user_id:
            raise ReviewForbiddenError(
                "user cannot review an order that belongs to another customer",
                details={"order_id": str(dto.order_id), "author_user_id": str(dto.author_user_id)},
            )

        if delivery.status != "completed":
            raise InvalidReviewDataError(
                "review can be created only after delivery completion",
                details={"order_id": str(dto.order_id), "delivery_status": delivery.status},
            )

        if order.restaurant_id != delivery.restaurant_id:
            raise InvalidReviewDataError(
                "order and delivery restaurant ids do not match",
                details={
                    "order_id": str(dto.order_id),
                    "order_restaurant_id": str(order.restaurant_id),
                    "delivery_restaurant_id": str(delivery.restaurant_id),
                },
            )

        if dto.target_type == ReviewTargetType.RESTAURANT:
            if dto.target_id != order.restaurant_id:
                raise InvalidReviewDataError(
                    "restaurant review target must match order restaurant",
                    details={
                        "order_id": str(dto.order_id),
                        "target_id": str(dto.target_id),
                        "restaurant_id": str(order.restaurant_id),
                    },
                )
        elif dto.target_type == ReviewTargetType.COURIER and dto.target_id != delivery.courier_id:
            raise InvalidReviewDataError(
                "courier review target must match assigned courier",
                details={
                    "order_id": str(dto.order_id),
                    "target_id": str(dto.target_id),
                    "courier_id": str(delivery.courier_id),
                },
            )

        review = Review.create(
            order_id=dto.order_id,
            author_user_id=dto.author_user_id,
            target_type=dto.target_type,
            target_id=dto.target_id,
            rating=Rating(dto.rating),
            comment=dto.comment,
        )
        created = await self._repository.create(review)
        return ReviewResponseDTO.from_entity(created)
