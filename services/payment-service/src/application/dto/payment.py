"""Payment DTO models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.reservation import PaymentReservation


class ReservePaymentDTO(BaseModel):
    """Input payload for payment reservation."""

    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str = "RUB"


class PaymentReservationResponseDTO(BaseModel):
    """Output payload for reservation state."""

    id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, reservation: PaymentReservation) -> "PaymentReservationResponseDTO":
        """Build response DTO from domain entity."""
        return cls(
            id=reservation.id,
            order_id=reservation.order_id,
            user_id=reservation.user_id,
            amount=reservation.amount,
            currency=reservation.currency,
            status=reservation.status.value,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
        )
