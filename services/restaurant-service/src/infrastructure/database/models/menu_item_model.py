"""MenuItemModel - SQLAlchemy ORM model for menu_items table."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects.availability import Availability
from src.domain.value_objects.category import Category
from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class MenuItemModel(Base):
    """SQLAlchemy model for menu_items table."""

    __tablename__ = "menu_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Menu item unique identifier",
    )

    restaurant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Restaurant ID",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Menu item name",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Menu item description",
    )

    price_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
        comment="Price amount",
    )

    price_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="RUB",
        comment="Currency code (ISO 4217)",
    )

    category: Mapped[Category] = mapped_column(
        Enum(Category, name="menu_category_enum", native_enum=True),
        nullable=False,
        index=True,
        comment="Menu item category",
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Image URL (optional)",
    )

    availability: Mapped[Availability] = mapped_column(
        Enum(Availability, name="menu_availability_enum", native_enum=True),
        nullable=False,
        default=Availability.AVAILABLE,
        index=True,
        comment="Item availability status",
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
            f"<MenuItemModel(id={self.id}, name={self.name}, "
            f"restaurant_id={self.restaurant_id}, category={self.category}, "
            f"availability={self.availability})>"
        )
