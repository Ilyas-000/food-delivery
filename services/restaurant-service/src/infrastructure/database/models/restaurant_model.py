"""RestaurantModel - SQLAlchemy ORM model for restaurants table."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects.cuisine import Cuisine
from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class RestaurantModel(Base):
    """SQLAlchemy model for restaurants table."""

    __tablename__ = "restaurants"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Restaurant unique identifier",
    )

    # No DB foreign key for microservices independence
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Restaurant owner ID (user service)",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Restaurant name",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Restaurant description",
    )

    street: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Street address",
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="City",
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Postal code",
    )

    latitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="GPS latitude (-90 to 90)",
    )

    longitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="GPS longitude (-180 to 180)",
    )

    cuisine: Mapped[Cuisine] = mapped_column(
        Enum(Cuisine, name="cuisine_enum", native_enum=True),
        nullable=False,
        index=True,
        comment="Cuisine type",
    )

    rating: Mapped[Decimal] = mapped_column(
        Numeric(precision=3, scale=2),
        nullable=False,
        default=Decimal("0.0"),
        index=True,
        comment="Average rating (0.0 to 5.0)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is restaurant active (soft delete)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
        comment="Creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        comment="Last update timestamp (UTC)",
    )

    def __repr__(self) -> str:
        return (
            f"<RestaurantModel(id={self.id}, name={self.name}, "
            f"cuisine={self.cuisine}, rating={self.rating}, is_active={self.is_active})>"
        )
