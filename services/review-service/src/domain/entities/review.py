"""Review aggregate root."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.value_objects.rating import Rating
from src.domain.value_objects.review_target import ReviewTargetType


@dataclass
class Review:
    """Review entity for supported target types."""

    id: UUID
    order_id: UUID
    author_user_id: UUID
    target_type: ReviewTargetType
    target_id: UUID
    rating: Rating
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        order_id: UUID,
        author_user_id: UUID,
        target_type: ReviewTargetType,
        target_id: UUID,
        rating: Rating,
        comment: str | None,
    ) -> "Review":
        """Create validated review entity."""
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            order_id=order_id,
            author_user_id=author_user_id,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            comment=_normalize_comment(comment),
            created_at=now,
            updated_at=now,
        )

    def update(self, *, rating: Rating | None = None, comment: str | None = None) -> None:
        """Update mutable review fields."""
        if rating is not None:
            self.rating = rating
        if comment is not None:
            self.comment = _normalize_comment(comment)
        self.updated_at = datetime.now(UTC)


def _normalize_comment(comment: str | None) -> str:
    """Normalize optional comment input."""
    normalized = (comment or "").strip()
    if len(normalized) > 1000:
        raise ValueError("comment must be 1000 characters or fewer")
    return normalized
