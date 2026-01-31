"""
Category Value Object.

Represents menu item category as an enum.
"""

from enum import Enum


class Category(str, Enum):
    """Menu item categories."""

    APPETIZER = "appetizer"
    SALAD = "salad"
    SOUP = "soup"
    MAIN_COURSE = "main_course"
    SIDE_DISH = "side_dish"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    ALCOHOL = "alcohol"
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    SPECIAL = "special"

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.replace("_", " ").title()
