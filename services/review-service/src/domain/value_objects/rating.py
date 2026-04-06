"""Rating value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    """Immutable restaurant rating value."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 1 or self.value > 5:
            raise ValueError("rating must be between 1 and 5")
