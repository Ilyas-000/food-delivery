"""
Cuisine Value Object.

Represents restaurant cuisine type as an enum.
"""

from enum import Enum


class Cuisine(str, Enum):
    """Restaurant cuisine types."""

    ITALIAN = "italian"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    INDIAN = "indian"
    MEXICAN = "mexican"
    AMERICAN = "american"
    FRENCH = "french"
    THAI = "thai"
    KOREAN = "korean"
    VIETNAMESE = "vietnamese"
    MEDITERRANEAN = "mediterranean"
    MIDDLE_EASTERN = "middle_eastern"
    GREEK = "greek"
    SPANISH = "spanish"
    TURKISH = "turkish"
    RUSSIAN = "russian"
    BRAZILIAN = "brazilian"
    FUSION = "fusion"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    SEAFOOD = "seafood"
    STEAKHOUSE = "steakhouse"
    FAST_FOOD = "fast_food"
    CAFE = "cafe"
    BAKERY = "bakery"
    DESSERTS = "desserts"
    OTHER = "other"

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.replace("_", " ").title()
