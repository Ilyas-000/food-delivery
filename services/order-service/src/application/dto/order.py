"""DTOs for order creation and saga context."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.order import Order
from src.domain.value_objects.order_item import OrderItem
from src.domain.value_objects.order_status import OrderStatus


class CreateOrderItemDTO(BaseModel):
    """Input line item for order creation."""

    menu_item_id: UUID
    quantity: int
    unit_price: Decimal
    currency: str = "RUB"


class CreateOrderDTO(BaseModel):
    """Input payload for CreateOrderUseCase."""

    user_id: UUID
    restaurant_id: UUID
    items: list[CreateOrderItemDTO]


class OrderResponseDTO(BaseModel):
    """Output payload for created/updated order."""

    id: UUID
    user_id: UUID
    restaurant_id: UUID
    status: OrderStatus
    total_amount: Decimal
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, order: Order) -> "OrderResponseDTO":
        """Build response DTO from domain entity."""
        return cls(
            id=order.id,
            user_id=order.user_id,
            restaurant_id=order.restaurant_id,
            status=order.status,
            total_amount=order.total_amount,
            cancellation_reason=order.cancellation_reason,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


@dataclass
class OrderSagaContext:
    """Mutable context passed through saga steps."""

    order_id: UUID
    user_id: UUID
    restaurant_id: UUID
    total_amount: Decimal
    items: tuple[OrderItem, ...]
    metadata: dict[str, str] = field(default_factory=dict)
