"""Review ORM model."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Return UTC timestamp."""
    return datetime.now(UTC)


class ReviewModel(Base):
    """SQLAlchemy model for reviews table."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "author_user_id",
            "target_type",
            name="uq_reviews_order_author_target_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    author_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
