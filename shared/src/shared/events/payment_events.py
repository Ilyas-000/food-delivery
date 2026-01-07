from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from .base import BaseEvent


class PaymentReservedEvent(BaseEvent):
    """Payment reserved event."""

    event_type: str = Field(default="payment.reserved", frozen=True)
    aggregate_type: str = Field(default="payment", frozen=True)

    order_id: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class PaymentCompletedEvent(BaseEvent):
    """Payment completed event."""

    event_type: str = Field(default="payment.completed", frozen=True)
    aggregate_type: str = Field(default="payment", frozen=True)

    order_id: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)


class PaymentFailedEvent(BaseEvent):
    """Payment failed event."""

    event_type: str = Field(default="payment.failed", frozen=True)
    aggregate_type: str = Field(default="payment", frozen=True)

    order_id: str
    reason: str
