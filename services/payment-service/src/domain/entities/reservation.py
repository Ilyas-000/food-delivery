"""Payment domain entity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from src.domain.value_objects.money import Money


class PaymentStatus(StrEnum):
    """Payment lifecycle status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    """Payment aggregate with lifecycle transitions."""

    id: UUID
    order_id: UUID
    user_id: UUID
    money: Money
    status: PaymentStatus
    idempotency_key: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        order_id: UUID,
        user_id: UUID,
        money: Money,
        idempotency_key: str | None = None,
    ) -> "Payment":
        """Create new payment with pending status."""
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            order_id=order_id,
            user_id=user_id,
            money=money,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )

    def confirm(self) -> None:
        """Confirm pending payment."""
        if self.status == PaymentStatus.COMPLETED:
            return
        if self.status is not PaymentStatus.PENDING:
            raise ValueError(f"cannot confirm payment in '{self.status.value}' status")

        self.status = PaymentStatus.COMPLETED
        self.updated_at = datetime.now(UTC)

    def release(self) -> None:
        """Release reserved funds for pending payment."""
        if self.status == PaymentStatus.FAILED:
            return
        if self.status is not PaymentStatus.PENDING:
            raise ValueError(f"cannot release payment in '{self.status.value}' status")

        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.now(UTC)

    def refund(self) -> None:
        """Refund completed payment."""
        if self.status == PaymentStatus.REFUNDED:
            return
        if self.status is not PaymentStatus.COMPLETED:
            raise ValueError(f"cannot refund payment in '{self.status.value}' status")

        self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.now(UTC)

    def matches_request(self, order_id: UUID, user_id: UUID, money: Money) -> bool:
        """Check whether request matches this payment data."""
        return (
            self.order_id == order_id
            and self.user_id == user_id
            and self.money.amount == money.amount
            and self.money.currency == money.currency
        )

    @property
    def amount(self) -> Decimal:
        """Expose amount for compatibility with existing DTO mapping."""
        return self.money.amount

    @property
    def currency(self) -> str:
        """Expose currency for compatibility with existing DTO mapping."""
        return self.money.currency


# Backward-compatible aliases for the reservation contract stage.
PaymentReservation = Payment
ReservationStatus = PaymentStatus
