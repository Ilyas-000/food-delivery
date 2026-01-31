"""
Availability Value Object.

Represents menu item availability status.
"""

from enum import Enum


class Availability(str, Enum):
    """Menu item availability status."""

    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @property
    def is_available(self) -> bool:
        """Check if item is available for ordering."""
        return self == Availability.AVAILABLE

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.replace("_", " ").title()
