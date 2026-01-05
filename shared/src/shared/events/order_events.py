from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from shared.events.base import BaseEvent


class OrderCreatedEvent(BaseEvent):
    """Emitted when an order is created in PENDING status."""

    event_type: str = "order.order.created"
    order_id: str
    user_id: str
    restaurant_id: str
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class OrderConfirmedEvent(BaseEvent):
    """Emitted when an order is confirmed after saga steps."""

    event_type: str = "order.order.confirmed"
    order_id: str


class OrderCancelledEvent(BaseEvent):
    """Emitted when an order is cancelled with an optional reason."""

    event_type: str = "order.order.cancelled"
    order_id: str
    reason: str | None = None
