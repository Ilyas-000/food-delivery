"""Payment DTO models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.reservation import Payment


class ReservePaymentDTO(BaseModel):
    """Input payload for payment reservation."""

    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str = "RUB"
    idempotency_key: str | None = None


class PaymentResponseDTO(BaseModel):
    """Output payload for payment state."""

    id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    idempotency_key: str | None = None

    @classmethod
    def from_entity(cls, payment: Payment) -> "PaymentResponseDTO":
        """Build response DTO from domain entity."""
        return cls(
            id=payment.id,
            order_id=payment.order_id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status.value,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            idempotency_key=payment.idempotency_key,
        )


class PaymentHistoryResponseDTO(BaseModel):
    """Output payload for payment history."""

    items: list[PaymentResponseDTO]
    total: int
