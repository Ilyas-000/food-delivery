"""Unit tests for rating value object and review entity."""

from uuid import uuid4

import pytest

from src.domain.entities.review import Review
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.review_target import ReviewTargetType


@pytest.mark.unit()
def test_rating_rejects_values_outside_range() -> None:
    with pytest.raises(ValueError, match="between 1 and 5"):
        Rating(0)

    with pytest.raises(ValueError, match="between 1 and 5"):
        Rating(6)


@pytest.mark.unit()
def test_review_create_normalizes_comment() -> None:
    review = Review.create(
        order_id=uuid4(),
        author_user_id=uuid4(),
        target_type=ReviewTargetType.RESTAURANT,
        target_id=uuid4(),
        rating=Rating(5),
        comment="  Great food  ",
    )

    assert review.comment == "Great food"
