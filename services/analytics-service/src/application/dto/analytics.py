"""Analytics DTO models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.analytics_event import AnalyticsEvent


class IngestAnalyticsEventDTO(BaseModel):
    """Normalized event DTO for ingestion."""

    event_id: UUID
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    user_id: str | None = None
    order_id: str | None = None
    restaurant_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    notification_type: str | None = None
    recipient: str | None = None
    template_name: str | None = None
    source_event_type: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AnalyticsEventResponseDTO(BaseModel):
    """DTO returned by event listing."""

    event_id: UUID
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    user_id: str | None = None
    order_id: str | None = None
    restaurant_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    notification_type: str | None = None
    recipient: str | None = None
    template_name: str | None = None
    source_event_type: str | None = None
    payload: dict[str, Any]

    @classmethod
    def from_entity(cls, event: AnalyticsEvent) -> AnalyticsEventResponseDTO:
        """Build DTO from domain entity."""
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            order_id=event.order_id,
            restaurant_id=event.restaurant_id,
            amount=event.amount,
            currency=event.currency,
            notification_type=event.notification_type,
            recipient=event.recipient,
            template_name=event.template_name,
            source_event_type=event.source_event_type,
            payload=event.payload,
        )


class AnalyticsEventListResponseDTO(BaseModel):
    """DTO returned by recent event listing."""

    items: list[AnalyticsEventResponseDTO]
    total: int


class AnalyticsOverviewDTO(BaseModel):
    """Operational metrics overview DTO."""

    total_events: int = 0
    orders_created: int = 0
    orders_confirmed: int = 0
    deliveries_assigned: int = 0
    emails_sent: int = 0
    pushes_sent: int = 0
    notifications_sent: int = 0
    gross_revenue: Decimal = Decimal("0.00")
    unique_customers: int = 0
    date_from: datetime | None = None
    date_to: datetime | None = None
