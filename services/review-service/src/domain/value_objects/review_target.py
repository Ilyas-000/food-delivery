"""Review target type definitions."""

from enum import StrEnum


class ReviewTargetType(StrEnum):
    """Supported review target categories."""

    RESTAURANT = "restaurant"
    COURIER = "courier"
