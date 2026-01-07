from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from .base import BaseEvent


class OrderCreatedEvent(BaseEvent):
    """Order created event."""

    event_type: str = Field(default="order.created", frozen=True)
    aggregate_type: str = Field(default="order", frozen=True)

    restaurant_id: str
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)

    @model_validator(mode="after")
    def ensure_user_id_set(self) -> OrderCreatedEvent:
        """Require user_id."""
        if not self.user_id:
            msg = "user_id is required for OrderCreatedEvent"
            raise ValueError(msg)
        return self


class OrderConfirmedEvent(BaseEvent):
    """Order confirmed event."""

    event_type: str = Field(default="order.confirmed", frozen=True)
    aggregate_type: str = Field(default="order", frozen=True)


class OrderCancelledEvent(BaseEvent):
    """Order cancelled event."""

    event_type: str = Field(default="order.cancelled", frozen=True)
    aggregate_type: str = Field(default="order", frozen=True)

    reason: str | None = None
