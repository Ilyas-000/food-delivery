"""
MenuItemModel - SQLAlchemy ORM model for menu_items table.

ORM Model vs Domain Entity:

ORM Model (MenuItemModel):
- Represents table in database
- Knows about SQLAlchemy, columns, indexes
- Simple data structure
- Persistence concern

Domain Entity (MenuItem):
- Represents business concept
- No database knowledge
- Contains business logic and methods
- Business concern

Repository Pattern connects them:
MenuItemModel <--(mapping)--> MenuItem Entity
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects import Availability, Category
from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class MenuItemModel(Base):
    """
    SQLAlchemy model for menu_items table.

    Uses SQLAlchemy 2.0 style with Mapped and mapped_column.

    Table structure:
    - id: UUID primary key
    - restaurant_id: UUID foreign key to restaurants
    - name: Item name
    - description: Item description
    - price_amount: Price amount (Decimal)
    - price_currency: Currency code (default RUB)
    - category: Enum (appetizer, main_course, etc.)
    - image_url: Optional image URL
    - availability: Enum (available, unavailable, discontinued)
    - created_at: Creation timestamp
    - updated_at: Update timestamp

    Indexes:
    - restaurant_id - for listing menu items by restaurant
    - category - for filtering by category
    - availability - for filtering available items
    - created_at - for sorting by creation date

    Note: This model is NOT used in domain/application layers!
    It is used only in infrastructure (repository).
    """

    __tablename__ = "menu_items"

    # Primary Key - UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Menu item unique identifier",
    )

    # Restaurant reference
    # We store UUID, but don't create DB foreign key to allow flexibility
    restaurant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,  # For listing items by restaurant
        comment="Restaurant ID",
    )

    # Item name
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Menu item name",
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Menu item description",
    )

    # Price components
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

    # Category - Enum
    category: Mapped[Category] = mapped_column(
        Enum(Category, name="menu_category_enum", native_enum=True),
        nullable=False,
        index=True,  # For filtering by category
        comment="Menu item category",
    )

    # Optional image URL
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Image URL (optional)",
    )

    # Availability - Enum
    availability: Mapped[Availability] = mapped_column(
        Enum(Availability, name="menu_availability_enum", native_enum=True),
        nullable=False,
        default=Availability.AVAILABLE,
        index=True,  # For filtering available items
        comment="Item availability status",
    )

    # Timestamps - always UTC!
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,  # For sorting
        comment="Creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,  # Auto-updates on UPDATE
        comment="Last update timestamp (UTC)",
    )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<MenuItemModel(id={self.id}, name={self.name}, "
            f"restaurant_id={self.restaurant_id}, category={self.category}, "
            f"availability={self.availability})>"
        )
