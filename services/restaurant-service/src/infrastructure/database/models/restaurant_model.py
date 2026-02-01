"""
RestaurantModel - SQLAlchemy ORM model for restaurants table.

ORM Model vs Domain Entity:

ORM Model (RestaurantModel):
- Represents table in database
- Knows about SQLAlchemy, columns, indexes
- Simple data structure
- Persistence concern

Domain Entity (Restaurant):
- Represents business concept
- No database knowledge
- Contains business logic and methods
- Business concern

Repository Pattern connects them:
RestaurantModel <--(mapping)--> Restaurant Entity
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.value_objects import Cuisine
from src.infrastructure.database.base import Base


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class RestaurantModel(Base):
    """
    SQLAlchemy model for restaurants table.

    Uses SQLAlchemy 2.0 style with Mapped and mapped_column.

    Table structure:
    - id: UUID primary key
    - owner_id: UUID foreign key to user service
    - name: Restaurant name
    - description: Restaurant description
    - street, city, postal_code: Address components
    - latitude, longitude: GPS coordinates (optional)
    - cuisine: Enum (italian, chinese, etc.)
    - rating: Decimal (0.0-5.0)
    - is_active: Soft delete flag
    - created_at: Creation timestamp
    - updated_at: Update timestamp

    Indexes:
    - owner_id - for listing restaurants by owner
    - cuisine - for filtering by cuisine type
    - city - for geographic filtering
    - rating - for sorting by rating
    - created_at - for sorting by creation date

    Note: This model is NOT used in domain/application layers!
    It is used only in infrastructure (repository).
    """

    __tablename__ = "restaurants"

    # Primary Key - UUID
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Restaurant unique identifier",
    )

    # Owner reference (foreign key to user service)
    # We store UUID, but don't create DB foreign key (microservices independence)
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Restaurant owner ID (user service)",
    )

    # Restaurant name
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Restaurant name",
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="Restaurant description",
    )

    # Address components
    street: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Street address",
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,  # For geographic filtering
        comment="City",
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Postal code",
    )

    # GPS coordinates (optional)
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

    # Cuisine type - Enum
    cuisine: Mapped[Cuisine] = mapped_column(
        Enum(Cuisine, name="cuisine_enum", native_enum=True),
        nullable=False,
        index=True,  # For filtering by cuisine
        comment="Cuisine type",
    )

    # Rating (0.0 to 5.0)
    # Using Numeric for precise decimal values
    rating: Mapped[Decimal] = mapped_column(
        Numeric(precision=3, scale=2),
        nullable=False,
        default=Decimal("0.0"),
        index=True,  # For sorting by rating
        comment="Average rating (0.0 to 5.0)",
    )

    # Soft delete flag
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is restaurant active (soft delete)",
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
            f"<RestaurantModel(id={self.id}, name={self.name}, "
            f"cuisine={self.cuisine}, rating={self.rating}, is_active={self.is_active})>"
        )
