"""API request and response schemas for orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.application.dto.order import OrderResponseDTO
from src.domain.value_objects.order_status import OrderStatus


class CreateOrderItemRequest(BaseModel):
    """Order line item payload."""

    menu_item_id: UUID
    quantity: int
    unit_price: Decimal
    currency: str = "RUB"


class CreateOrderRequest(BaseModel):
    """Order creation payload."""

    user_id: UUID
    restaurant_id: UUID
    items: list[CreateOrderItemRequest]


class OrderResponse(BaseModel):
    """Order response payload."""

    id: UUID
    user_id: UUID
    restaurant_id: UUID
    status: OrderStatus
    total_amount: Decimal
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: OrderResponseDTO) -> "OrderResponse":
        """Build API response from application DTO."""
        return cls(
            id=dto.id,
            user_id=dto.user_id,
            restaurant_id=dto.restaurant_id,
            status=dto.status,
            total_amount=dto.total_amount,
            cancellation_reason=dto.cancellation_reason,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
