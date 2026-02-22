"""
Menu item-related domain exceptions.
"""

from typing import Any

from src.domain.exceptions.base import DomainError


class MenuItemNotFoundError(DomainError):
    """Raised when menu item is not found."""

    def __init__(self, menu_item_id: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Menu item with ID {menu_item_id} not found",
            details=details or {"menu_item_id": menu_item_id},
        )


class MenuItemNotInRestaurantError(DomainError):
    """Raised when menu item doesn't belong to restaurant."""

    def __init__(
        self, menu_item_id: str, restaurant_id: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Menu item {menu_item_id} does not belong to restaurant {restaurant_id}",
            details=details or {"menu_item_id": menu_item_id, "restaurant_id": restaurant_id},
        )


class InvalidMenuItemDataError(DomainError):
    """Raised when menu item data is invalid."""

    def __init__(self, field: str, reason: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Invalid {field}: {reason}",
            details=details or {"field": field, "reason": reason},
        )
