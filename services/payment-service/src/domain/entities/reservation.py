"""Payment reservation domain entity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class ReservationStatus(StrEnum):
    """Reservation lifecycle status."""

    RESERVED = "reserved"
    RELEASED = "released"


@dataclass
class PaymentReservation:
    """Reservation aggregate for order payment hold."""

    id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        order_id: UUID,
        user_id: UUID,
        amount: Decimal,
        currency: str,
    ) -> "PaymentReservation":
        """Create new reservation with initial status."""
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            order_id=order_id,
            user_id=user_id,
            amount=amount.quantize(Decimal("0.01")),
            currency=currency,
            status=ReservationStatus.RESERVED,
            created_at=now,
            updated_at=now,
        )

    def release(self) -> None:
        """Release previously reserved funds."""
        self.status = ReservationStatus.RELEASED
        self.updated_at = datetime.now(UTC)
