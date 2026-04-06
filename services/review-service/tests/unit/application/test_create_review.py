"""Unit tests for create review use case."""

from uuid import UUID, uuid4

import pytest

from src.application.dto.review import CreateReviewDTO, DeliverySnapshotDTO, OrderSnapshotDTO
from src.application.interfaces.review_repository import IReviewRepository
from src.application.interfaces.validation_clients import (
    IDeliveryValidationClient,
    IOrderValidationClient,
)
from src.application.use_cases.create_review import CreateReviewUseCase
from src.domain.entities.review import Review
from src.domain.exceptions.base import (
    InvalidReviewDataError,
    ReviewAlreadyExistsError,
    ReviewForbiddenError,
)
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.review_target import ReviewTargetType


class InMemoryReviewRepository(IReviewRepository):
    """Simple repository for use case unit tests."""

    def __init__(self) -> None:
        self.items: dict[UUID, Review] = {}

    async def create(self, review: Review) -> Review:
        self.items[review.id] = review
        return review

    async def get_by_id(self, review_id: UUID) -> Review | None:
        return self.items.get(review_id)

    async def get_by_order_author_and_target(
        self,
        order_id: UUID,
        author_user_id: UUID,
        target_type: ReviewTargetType,
    ) -> Review | None:
        return next(
            (
                review
                for review in self.items.values()
                if review.order_id == order_id
                and review.author_user_id == author_user_id
                and review.target_type == target_type
            ),
            None,
        )

    async def list_reviews(
        self,
        *,
        restaurant_id: UUID | None,
        courier_id: UUID | None,
        author_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Review], int]:
        _ = restaurant_id, courier_id, author_user_id, limit, offset
        return [], 0

    async def update(self, review: Review) -> Review:
        self.items[review.id] = review
        return review

    async def delete(self, review_id: UUID) -> None:
        self.items.pop(review_id, None)

    async def get_restaurant_rating(self, restaurant_id: UUID):  # pragma: no cover - not used here
        _ = restaurant_id
        raise NotImplementedError

    async def get_courier_rating(self, courier_id: UUID):  # pragma: no cover - not used here
        _ = courier_id
        raise NotImplementedError


class StubOrderClient(IOrderValidationClient):
    """Configurable order client stub."""

    def __init__(self, *, user_id: UUID, restaurant_id: UUID) -> None:
        self._user_id = user_id
        self._restaurant_id = restaurant_id

    async def get_order(self, order_id: UUID) -> OrderSnapshotDTO:
        return OrderSnapshotDTO(
            order_id=order_id,
            user_id=self._user_id,
            restaurant_id=self._restaurant_id,
            status="confirmed",
        )


class StubDeliveryClient(IDeliveryValidationClient):
    """Configurable delivery client stub."""

    def __init__(self, *, restaurant_id: UUID, courier_id: UUID, status: str) -> None:
        self._restaurant_id = restaurant_id
        self._courier_id = courier_id
        self._status = status

    async def get_delivery(self, order_id: UUID) -> DeliverySnapshotDTO:
        return DeliverySnapshotDTO(
            assignment_id=uuid4(),
            order_id=order_id,
            restaurant_id=self._restaurant_id,
            courier_id=self._courier_id,
            status=self._status,
            delivered_at=None,
        )


EXPECTED_RATING = 5


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_review_success() -> None:
    user_id = uuid4()
    restaurant_id = uuid4()
    courier_id = uuid4()
    repository = InMemoryReviewRepository()
    use_case = CreateReviewUseCase(
        repository=repository,
        order_client=StubOrderClient(user_id=user_id, restaurant_id=restaurant_id),
        delivery_client=StubDeliveryClient(
            restaurant_id=restaurant_id,
            courier_id=courier_id,
            status="completed",
        ),
    )

    result = await use_case.execute(
        CreateReviewDTO(
            order_id=uuid4(),
            author_user_id=user_id,
            target_type=ReviewTargetType.RESTAURANT,
            target_id=restaurant_id,
            rating=EXPECTED_RATING,
            comment="Great",
        )
    )

    assert result.rating == EXPECTED_RATING
    assert result.target_type == ReviewTargetType.RESTAURANT
    assert result.target_id == restaurant_id


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_review_rejects_duplicate() -> None:
    user_id = uuid4()
    restaurant_id = uuid4()
    courier_id = uuid4()
    order_id = uuid4()
    repository = InMemoryReviewRepository()
    repository.items[uuid4()] = Review.create(
        order_id=order_id,
        author_user_id=user_id,
        target_type=ReviewTargetType.RESTAURANT,
        target_id=restaurant_id,
        rating=Rating(5),
        comment="Existing",
    )
    use_case = CreateReviewUseCase(
        repository=repository,
        order_client=StubOrderClient(user_id=user_id, restaurant_id=restaurant_id),
        delivery_client=StubDeliveryClient(
            restaurant_id=restaurant_id,
            courier_id=courier_id,
            status="completed",
        ),
    )

    with pytest.raises(ReviewAlreadyExistsError):
        await use_case.execute(
            CreateReviewDTO(
                order_id=order_id,
                author_user_id=user_id,
                target_type=ReviewTargetType.RESTAURANT,
                target_id=restaurant_id,
                rating=4,
                comment="Again",
            )
        )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_review_rejects_foreign_order() -> None:
    author_user_id = uuid4()
    repository = InMemoryReviewRepository()
    use_case = CreateReviewUseCase(
        repository=repository,
        order_client=StubOrderClient(user_id=uuid4(), restaurant_id=uuid4()),
        delivery_client=StubDeliveryClient(
            restaurant_id=uuid4(),
            courier_id=uuid4(),
            status="completed",
        ),
    )

    with pytest.raises(ReviewForbiddenError):
        await use_case.execute(
            CreateReviewDTO(
                order_id=uuid4(),
                author_user_id=author_user_id,
                target_type=ReviewTargetType.RESTAURANT,
                target_id=uuid4(),
                rating=5,
                comment="Nope",
            )
        )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_review_requires_completed_delivery() -> None:
    user_id = uuid4()
    restaurant_id = uuid4()
    courier_id = uuid4()
    repository = InMemoryReviewRepository()
    use_case = CreateReviewUseCase(
        repository=repository,
        order_client=StubOrderClient(user_id=user_id, restaurant_id=restaurant_id),
        delivery_client=StubDeliveryClient(
            restaurant_id=restaurant_id,
            courier_id=courier_id,
            status="assigned",
        ),
    )

    with pytest.raises(InvalidReviewDataError):
        await use_case.execute(
            CreateReviewDTO(
                order_id=uuid4(),
                author_user_id=user_id,
                target_type=ReviewTargetType.RESTAURANT,
                target_id=restaurant_id,
                rating=5,
                comment="Early",
            )
        )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_courier_review_success() -> None:
    user_id = uuid4()
    restaurant_id = uuid4()
    courier_id = uuid4()
    repository = InMemoryReviewRepository()
    use_case = CreateReviewUseCase(
        repository=repository,
        order_client=StubOrderClient(user_id=user_id, restaurant_id=restaurant_id),
        delivery_client=StubDeliveryClient(
            restaurant_id=restaurant_id,
            courier_id=courier_id,
            status="completed",
        ),
    )

    result = await use_case.execute(
        CreateReviewDTO(
            order_id=uuid4(),
            author_user_id=user_id,
            target_type=ReviewTargetType.COURIER,
            target_id=courier_id,
            rating=5,
            comment="Fast and polite",
        )
    )

    assert result.target_type == ReviewTargetType.COURIER
    assert result.target_id == courier_id
