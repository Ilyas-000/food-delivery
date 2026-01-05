from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from shared.events.base import BaseEvent


class PaymentReservedEvent(BaseEvent):
    """Emitted when payment funds are reserved."""

    event_type: str = "payment.payment.reserved"
    payment_id: str
    order_id: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class PaymentFailedEvent(BaseEvent):
    """Emitted when payment reservation fails."""

    event_type: str = "payment.payment.failed"
    payment_id: str
    order_id: str
    reason: str
