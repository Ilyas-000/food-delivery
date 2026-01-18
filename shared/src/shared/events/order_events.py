from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from annotated_types import Ge, MaxLen, MinLen
from pydantic import model_validator

from shared.events.base import BaseEvent


class OrderCreatedEvent(BaseEvent):
    """Order created event."""

    event_type: Literal["order-service.order.created"] = "order-service.order.created"
    aggregate_type: Literal["order"] = "order"

    restaurant_id: str
    total_amount: Annotated[Decimal, Ge(0)]
    currency: Annotated[str, MinLen(3), MaxLen(3)] = "RUB"

    @model_validator(mode="after")
    def ensure_user_id_set(self) -> OrderCreatedEvent:
        """Require user_id."""
        if not self.user_id:
            msg = "user_id is required for OrderCreatedEvent"
            raise ValueError(msg)
        return self


class OrderConfirmedEvent(BaseEvent):
    """Order confirmed event."""

    event_type: Literal["order-service.order.confirmed"] = "order-service.order.confirmed"
    aggregate_type: Literal["order"] = "order"


class OrderCancelledEvent(BaseEvent):
    """Order cancelled event."""

    event_type: Literal["order-service.order.cancelled"] = "order-service.order.cancelled"
    aggregate_type: Literal["order"] = "order"

    reason: str | None = None
