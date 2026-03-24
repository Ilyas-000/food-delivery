"""Order item value object."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class OrderItem:
    """Immutable line item inside an order."""

    menu_item_id: UUID
    quantity: int
    unit_price: Decimal
    currency: str = "RUB"

    def __post_init__(self) -> None:
        """Validate item values."""
        if self.quantity < 1:
            raise ValueError("quantity must be greater than zero")
        if self.unit_price <= Decimal("0"):
            raise ValueError("unit_price must be greater than zero")
        if self.unit_price.as_tuple().exponent < -2:  # type: ignore[operator]
            raise ValueError("unit_price can have at most 2 decimal places")
        if self.currency != "RUB":
            raise ValueError("unsupported currency")

        object.__setattr__(self, "unit_price", self.unit_price.quantize(Decimal("0.01")))

    @property
    def total_amount(self) -> Decimal:
        """Return total amount for this line item."""
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))
