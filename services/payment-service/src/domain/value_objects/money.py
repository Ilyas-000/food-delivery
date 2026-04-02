"""Money value object for payment operations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Money:
    """Immutable payment amount with currency."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        """Validate amount and normalize currency."""
        try:
            normalized_amount = Decimal(str(self.amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("amount must be a valid decimal value") from exc

        if normalized_amount <= Decimal("0"):
            raise ValueError("amount must be greater than zero")

        normalized_currency = self.currency.strip().upper()
        if len(normalized_currency) != 3 or not normalized_currency.isalpha():
            raise ValueError("currency must be a 3-letter alphabetic code")

        object.__setattr__(self, "amount", normalized_amount)
        object.__setattr__(self, "currency", normalized_currency)
