"""API schemas for payment endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.payment import PaymentHistoryResponseDTO, PaymentResponseDTO


class ReservePaymentRequest(BaseModel):
    """Request schema for reserving payment."""

    order_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = "RUB"


class PaymentResponse(BaseModel):
    """Response schema for payment."""

    payment_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    idempotency_key: str | None = None

    @classmethod
    def from_dto(cls, dto: PaymentResponseDTO) -> "PaymentResponse":
        """Build API response from DTO."""
        return cls(
            payment_id=dto.id,
            order_id=dto.order_id,
            user_id=dto.user_id,
            amount=dto.amount,
            currency=dto.currency,
            status=dto.status,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            idempotency_key=dto.idempotency_key,
        )


class PaymentReservationResponse(BaseModel):
    """Backward-compatible response schema for reservation endpoint."""

    reservation_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: PaymentResponseDTO) -> "PaymentReservationResponse":
        """Build API response from DTO."""
        status = "reserved" if dto.status == "pending" else dto.status
        return cls(
            reservation_id=dto.id,
            order_id=dto.order_id,
            user_id=dto.user_id,
            amount=dto.amount,
            currency=dto.currency,
            status=status,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class PaymentHistoryResponse(BaseModel):
    """Response schema for payment history."""

    items: list[PaymentResponse]
    total: int

    @classmethod
    def from_dto(cls, dto: PaymentHistoryResponseDTO) -> "PaymentHistoryResponse":
        """Build history response from DTO."""
        return cls(
            items=[PaymentResponse.from_dto(item) for item in dto.items],
            total=dto.total,
        )
