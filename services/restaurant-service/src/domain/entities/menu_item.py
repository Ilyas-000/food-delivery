"""
MenuItem Entity.

Represents a menu item in a restaurant.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.exceptions.menu_item import InvalidMenuItemDataError
from src.domain.value_objects.availability import Availability
from src.domain.value_objects.category import Category
from src.domain.value_objects.price import Price


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


@dataclass
class MenuItem:
    """
    MenuItem entity.

    Business rules:
    - Name: 2-200 characters
    - Description: 0-1000 characters
    - Price: Must be positive
    - Availability can be toggled (available/out_of_stock/discontinued)
    - Discontinued items cannot be made available again
    - Image URL is optional

    Examples:
        >>> from decimal import Decimal
        >>> item = MenuItem.create(
        ...     restaurant_id=uuid4(),
        ...     name="Margherita Pizza",
        ...     description="Classic pizza with tomatoes and mozzarella",
        ...     price=Price(Decimal("450.00")),
        ...     category=Category.MAIN_COURSE
        ... )
        >>> item.availability
        <Availability.AVAILABLE: 'available'>
        >>> item.mark_unavailable()
        >>> item.availability
        <Availability.OUT_OF_STOCK: 'out_of_stock'>
    """

    id: UUID
    restaurant_id: UUID
    name: str
    description: str
    price: Price
    category: Category
    image_url: str | None
    availability: Availability
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        restaurant_id: UUID,
        name: str,
        description: str,
        price: Price,
        category: Category,
        image_url: str | None = None,
    ) -> "MenuItem":
        """
        Factory method to create a new menu item.

        Args:
            restaurant_id: ID of restaurant this item belongs to
            name: Item name (2-200 characters)
            description: Item description (0-1000 characters)
            price: Item price (Price Value Object)
            category: Item category (Enum)
            image_url: Optional image URL

        Returns:
            MenuItem: New menu item entity

        Raises:
            InvalidMenuItemDataError: If validation fails

        Business rules enforced:
        - Name must be 2-200 characters
        - Description max 1000 characters
        - Price must be positive (enforced by Price VO)
        - New items are available by default
        """
        # Validate name
        if not name or len(name) < 2:
            raise InvalidMenuItemDataError("name", "must be at least 2 characters")
        if len(name) > 200:
            raise InvalidMenuItemDataError("name", "must be at most 200 characters")

        # Validate description
        if len(description) > 1000:
            raise InvalidMenuItemDataError("description", "must be at most 1000 characters")

        # Validate image URL (if provided)
        if image_url is not None and len(image_url) > 500:
            raise InvalidMenuItemDataError("image_url", "must be at most 500 characters")

        # Create menu item
        return cls(
            id=uuid4(),
            restaurant_id=restaurant_id,
            name=name.strip(),
            description=description.strip(),
            price=price,
            category=category,
            image_url=image_url,
            availability=Availability.AVAILABLE,  # New items are available
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    def update_info(
        self,
        name: str | None = None,
        description: str | None = None,
        price: Price | None = None,
        category: Category | None = None,
        image_url: str | None = None,
    ) -> None:
        """
        Update menu item information.

        Args:
            name: New name (optional)
            description: New description (optional)
            price: New price (optional)
            category: New category (optional)
            image_url: New image URL (optional)

        Raises:
            InvalidMenuItemDataError: If validation fails

        Business rules:
        - Same validation as create()
        - Only provided fields are updated
        - updated_at is always set to current time
        """
        if name is not None:
            if len(name) < 2:
                raise InvalidMenuItemDataError("name", "must be at least 2 characters")
            if len(name) > 200:
                raise InvalidMenuItemDataError("name", "must be at most 200 characters")
            self.name = name.strip()

        if description is not None:
            if len(description) > 1000:
                raise InvalidMenuItemDataError("description", "must be at most 1000 characters")
            self.description = description.strip()

        if price is not None:
            self.price = price

        if category is not None:
            self.category = category

        if image_url is not None:
            if len(image_url) > 500:
                raise InvalidMenuItemDataError("image_url", "must be at most 500 characters")
            self.image_url = image_url

        self.updated_at = _utc_now()

    def mark_available(self) -> None:
        """
        Mark item as available for ordering.

        Business rule:
        - Cannot make discontinued items available
        - Can make out_of_stock items available again
        """
        if self.availability == Availability.DISCONTINUED:
            raise InvalidMenuItemDataError(
                "availability", "cannot make discontinued item available"
            )

        self.availability = Availability.AVAILABLE
        self.updated_at = _utc_now()

    def mark_unavailable(self) -> None:
        """
        Mark item as temporarily out of stock.

        Business rule:
        - Item can be made available again later
        - Different from discontinued (which is permanent)
        """
        self.availability = Availability.OUT_OF_STOCK
        self.updated_at = _utc_now()

    def discontinue(self) -> None:
        """
        Permanently discontinue this item.

        Business rule:
        - Discontinued items cannot be made available again
        - Used when item is removed from menu permanently
        - Soft delete (item still exists in DB for order history)
        """
        self.availability = Availability.DISCONTINUED
        self.updated_at = _utc_now()

    @property
    def is_available(self) -> bool:
        """Check if item is available for ordering."""
        return self.availability == Availability.AVAILABLE

    def __eq__(self, other: object) -> bool:
        """
        Entity equality by ID.

        Two menu items are equal if they have the same ID.
        """
        if not isinstance(other, MenuItem):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Entity hash by ID."""
        return hash(self.id)

    def __str__(self) -> str:
        """String representation."""
        return f"MenuItem(id={self.id}, name='{self.name}', price={self.price})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"MenuItem(id={self.id}, restaurant_id={self.restaurant_id}, "
            f"name='{self.name}', price={self.price}, category={self.category}, "
            f"availability={self.availability})"
        )
