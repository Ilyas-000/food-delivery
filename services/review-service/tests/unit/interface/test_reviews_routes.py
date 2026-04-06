"""Unit tests for review routes."""

from decimal import Decimal
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from src.application.dto.review import CourierRatingDTO, RestaurantRatingDTO
from src.application.use_cases.get_courier_rating import GetCourierRatingUseCase
from src.application.use_cases.get_restaurant_rating import GetRestaurantRatingUseCase
from src.application.use_cases.update_review import UpdateReviewUseCase
from src.domain.value_objects.review_target import ReviewTargetType
from src.interface.dependencies.review import (
    get_courier_rating_use_case,
    get_restaurant_rating_use_case,
    get_update_review_use_case,
)
from src.main import app


class StubRestaurantRatingUseCase(GetRestaurantRatingUseCase):
    """Stub use case for route-level rating test."""

    def __init__(self) -> None:
        pass

    async def execute(self, restaurant_id):  # type: ignore[no-untyped-def]
        return RestaurantRatingDTO(
            restaurant_id=restaurant_id,
            average_rating=Decimal("4.50"),
            reviews_count=2,
        )


class StubCourierRatingUseCase(GetCourierRatingUseCase):
    """Stub use case for courier rating route."""

    def __init__(self) -> None:
        pass

    async def execute(self, courier_id):  # type: ignore[no-untyped-def]
        return CourierRatingDTO(
            courier_id=courier_id,
            average_rating=Decimal("4.80"),
            reviews_count=3,
        )


class StubUpdateReviewUseCase(UpdateReviewUseCase):
    """Stub use case for payload validation test."""

    def __init__(self) -> None:
        pass


@pytest.mark.unit()
def test_create_review_endpoint_requires_identity() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/reviews",
        json={
            "order_id": str(uuid4()),
            "target_type": ReviewTargetType.RESTAURANT,
            "target_id": str(uuid4()),
            "rating": 5,
            "comment": "Great",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.unit()
def test_review_update_requires_payload() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_update_review_use_case] = StubUpdateReviewUseCase

    try:
        response = client.patch(
            f"/api/v1/reviews/{uuid4()}",
            json={},
            headers={"X-User-ID": str(uuid4())},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit()
def test_restaurant_rating_endpoint_returns_success() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_restaurant_rating_use_case] = StubRestaurantRatingUseCase

    try:
        response = client.get(f"/api/v1/reviews/restaurants/{uuid4()}/rating")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["average_rating"] == "4.50"


@pytest.mark.unit()
def test_courier_rating_endpoint_returns_success() -> None:
    client = TestClient(app)
    app.dependency_overrides[get_courier_rating_use_case] = StubCourierRatingUseCase

    try:
        response = client.get(f"/api/v1/reviews/couriers/{uuid4()}/rating")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["average_rating"] == "4.80"
