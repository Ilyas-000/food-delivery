"""
Price Value Object.

Immutable monetary value with currency and validation.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Price:
    """
    Price value object.

    Business rules:
    - Amount must be non-negative
    - Amount has max 2 decimal places
    - Currency is always RUB (can be extended later)
    - Immutable (frozen dataclass)

    Examples:
        >>> price = Price(Decimal("100.50"))
        >>> price.amount
        Decimal('100.50')
        >>> price.currency
        'RUB'
    """

    amount: Decimal
    currency: str = "RUB"

    def __post_init__(self) -> None:
        """Validate price after initialization."""
        # Validate amount is non-negative
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative")

        # Validate decimal places (max 2)
        if self.amount.as_tuple().exponent < -2:  # type: ignore[operator]
            raise ValueError("Price amount can have at most 2 decimal places")

        # Normalize to 2 decimal places
        object.__setattr__(self, "amount", self.amount.quantize(Decimal("0.01")))

        # Validate currency (for now only RUB)
        if self.currency != "RUB":
            raise ValueError(f"Unsupported currency: {self.currency}. Only RUB is supported.")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.amount} {self.currency}"

    def __add__(self, other: "Price") -> "Price":
        """Add two prices."""
        if not isinstance(other, Price):
            raise TypeError("Can only add Price to Price")
        if self.currency != other.currency:
            raise ValueError("Cannot add prices with different currencies")
        return Price(self.amount + other.amount, self.currency)

    def __mul__(self, multiplier: int | Decimal) -> "Price":
        """Multiply price by a number."""
        if not isinstance(multiplier, int | Decimal):
            raise TypeError("Can only multiply Price by int or Decimal")
        return Price(self.amount * Decimal(multiplier), self.currency)

    def __lt__(self, other: "Price") -> bool:
        """Less than comparison."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price to Price")
        if self.currency != other.currency:
            raise ValueError("Cannot compare prices with different currencies")
        return self.amount < other.amount

    def __le__(self, other: "Price") -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price to Price")
        if self.currency != other.currency:
            raise ValueError("Cannot compare prices with different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: "Price") -> bool:
        """Greater than comparison."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price to Price")
        if self.currency != other.currency:
            raise ValueError("Cannot compare prices with different currencies")
        return self.amount > other.amount

    def __ge__(self, other: "Price") -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, Price):
            raise TypeError("Can only compare Price to Price")
        if self.currency != other.currency:
            raise ValueError("Cannot compare prices with different currencies")
        return self.amount >= other.amount
