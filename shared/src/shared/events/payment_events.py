from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from annotated_types import Ge, MaxLen, MinLen

from .base import BaseEvent


class PaymentReservedEvent(BaseEvent):
    """Payment reserved event."""

    event_type: Literal["payment-service.payment.reserved"] = "payment-service.payment.reserved"
    aggregate_type: Literal["payment"] = "payment"

    order_id: str
    amount: Annotated[Decimal, Ge(0)]
    currency: Annotated[str, MinLen(3), MaxLen(3)] = "RUB"


class PaymentCompletedEvent(BaseEvent):
    """Payment completed event."""

    event_type: Literal["payment-service.payment.completed"] = "payment-service.payment.completed"
    aggregate_type: Literal["payment"] = "payment"

    order_id: str
    amount: Annotated[Decimal, Ge(0)]
    currency: Annotated[str, MinLen(3), MaxLen(3)] = "RUB"


class PaymentFailedEvent(BaseEvent):
    """Payment failed event."""

    event_type: Literal["payment-service.payment.failed"] = "payment-service.payment.failed"
    aggregate_type: Literal["payment"] = "payment"

    order_id: str
    reason: str
