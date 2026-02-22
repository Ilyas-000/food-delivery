"""
Restaurant-related domain exceptions.
"""

from typing import Any

from src.domain.exceptions.base import DomainError


class RestaurantNotFoundError(DomainError):
    """Raised when restaurant is not found."""

    def __init__(self, restaurant_id: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Restaurant with ID {restaurant_id} not found",
            details=details or {"restaurant_id": restaurant_id},
        )


class RestaurantAlreadyExistsError(DomainError):
    """Raised when restaurant with same name already exists for owner."""

    def __init__(self, name: str, owner_id: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Restaurant '{name}' already exists for this owner",
            details=details or {"name": name, "owner_id": owner_id},
        )


class RestaurantNotOwnedByUserError(DomainError):
    """Raised when user tries to modify restaurant they don't own."""

    def __init__(
        self, restaurant_id: str, user_id: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Restaurant {restaurant_id} is not owned by user {user_id}",
            details=details or {"restaurant_id": restaurant_id, "user_id": user_id},
        )


class InvalidRestaurantDataError(DomainError):
    """Raised when restaurant data is invalid."""

    def __init__(self, field: str, reason: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"Invalid {field}: {reason}",
            details=details or {"field": field, "reason": reason},
        )
