"""
Restaurant Entity.

Aggregate root for restaurant domain.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.exceptions import InvalidRestaurantDataError
from src.domain.value_objects import Address, Cuisine


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


@dataclass
class Restaurant:
    """
    Restaurant entity (Aggregate Root).

    Business rules:
    - Name: 2-100 characters
    - Description: 0-1000 characters
    - Rating: 0.0-5.0 (calculated from reviews, not set directly)
    - New restaurants start with rating 0.0
    - Only owner can modify restaurant
    - Deactivated restaurants are hidden from customers

    Examples:
        >>> address = Address("123 Main St", "Moscow", "101000")
        >>> restaurant = Restaurant.create(
        ...     owner_id=uuid4(),
        ...     name="Best Pizza",
        ...     description="Amazing Italian pizza",
        ...     address=address,
        ...     cuisine=Cuisine.ITALIAN
        ... )
        >>> restaurant.is_active
        True
        >>> restaurant.rating
        Decimal('0.0')
    """

    id: UUID
    owner_id: UUID
    name: str
    description: str
    address: Address
    cuisine: Cuisine
    rating: Decimal
    is_active: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        owner_id: UUID,
        name: str,
        description: str,
        address: Address,
        cuisine: Cuisine,
    ) -> "Restaurant":
        """
        Factory method to create a new restaurant.

        Args:
            owner_id: ID of restaurant owner (from User Service)
            name: Restaurant name (2-100 characters)
            description: Restaurant description (0-1000 characters)
            address: Restaurant address (Value Object)
            cuisine: Cuisine type (Enum)

        Returns:
            Restaurant: New restaurant entity

        Raises:
            InvalidRestaurantDataError: If validation fails

        Business rules enforced:
        - Name must be 2-100 characters
        - Description max 1000 characters
        - New restaurants start with rating 0.0
        - New restaurants are active by default
        """
        # Validate name
        if not name or len(name) < 2:
            raise InvalidRestaurantDataError("name", "must be at least 2 characters")
        if len(name) > 100:
            raise InvalidRestaurantDataError("name", "must be at most 100 characters")

        # Validate description
        if len(description) > 1000:
            raise InvalidRestaurantDataError("description", "must be at most 1000 characters")

        # Create restaurant
        return cls(
            id=uuid4(),
            owner_id=owner_id,
            name=name.strip(),
            description=description.strip(),
            address=address,
            cuisine=cuisine,
            rating=Decimal("0.0"),  # New restaurants start with 0 rating
            is_active=True,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    def update_info(
        self,
        name: str | None = None,
        description: str | None = None,
        address: Address | None = None,
        cuisine: Cuisine | None = None,
    ) -> None:
        """
        Update restaurant information.

        Args:
            name: New name (optional)
            description: New description (optional)
            address: New address (optional)
            cuisine: New cuisine (optional)

        Raises:
            InvalidRestaurantDataError: If validation fails

        Business rules:
        - Same validation as create()
        - Only provided fields are updated
        - updated_at is always set to current time
        """
        if name is not None:
            if len(name) < 2:
                raise InvalidRestaurantDataError("name", "must be at least 2 characters")
            if len(name) > 100:
                raise InvalidRestaurantDataError("name", "must be at most 100 characters")
            self.name = name.strip()

        if description is not None:
            if len(description) > 1000:
                raise InvalidRestaurantDataError("description", "must be at most 1000 characters")
            self.description = description.strip()

        if address is not None:
            self.address = address

        if cuisine is not None:
            self.cuisine = cuisine

        self.updated_at = _utc_now()

    def update_rating(self, new_rating: Decimal) -> None:
        """
        Update restaurant rating.

        Args:
            new_rating: New rating (0.0-5.0)

        Raises:
            InvalidRestaurantDataError: If rating is out of range

        Note:
            This is called by Review Service after new review is added.
            Rating is calculated as average of all reviews.
        """
        if not 0 <= new_rating <= 5:
            raise InvalidRestaurantDataError("rating", f"must be between 0 and 5, got {new_rating}")

        self.rating = new_rating.quantize(Decimal("0.1"))  # Round to 1 decimal place
        self.updated_at = _utc_now()

    def activate(self) -> None:
        """
        Activate restaurant (make visible to customers).

        Business rule:
        - Only owner can activate/deactivate restaurant
        - Activated restaurants appear in search results
        """
        self.is_active = True
        self.updated_at = _utc_now()

    def deactivate(self) -> None:
        """
        Deactivate restaurant (hide from customers).

        Business rule:
        - Deactivated restaurants don't appear in search
        - Existing orders can still be fulfilled
        - Restaurant can be reactivated later
        """
        self.is_active = False
        self.updated_at = _utc_now()

    def __eq__(self, other: object) -> bool:
        """
        Entity equality by ID.

        Two restaurants are equal if they have the same ID.
        """
        if not isinstance(other, Restaurant):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Entity hash by ID."""
        return hash(self.id)

    def __str__(self) -> str:
        """String representation."""
        return f"Restaurant(id={self.id}, name='{self.name}', cuisine={self.cuisine})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Restaurant(id={self.id}, owner_id={self.owner_id}, name='{self.name}', "
            f"cuisine={self.cuisine}, rating={self.rating}, is_active={self.is_active})"
        )
