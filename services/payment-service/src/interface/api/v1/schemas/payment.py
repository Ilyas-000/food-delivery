"""API schemas for payment endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.payment import PaymentReservationResponseDTO


class ReservePaymentRequest(BaseModel):
    """Request schema for reserving payment."""

    order_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = "RUB"


class PaymentReservationResponse(BaseModel):
    """Response schema for payment reservation."""

    reservation_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: PaymentReservationResponseDTO) -> "PaymentReservationResponse":
        """Build API response from DTO."""
        return cls(
            reservation_id=dto.id,
            order_id=dto.order_id,
            user_id=dto.user_id,
            amount=dto.amount,
            currency=dto.currency,
            status=dto.status,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
