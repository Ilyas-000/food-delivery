"""Analytics API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.application.dto.analytics import (
    AnalyticsEventListResponseDTO,
    AnalyticsEventResponseDTO,
    AnalyticsOverviewDTO,
)


class AnalyticsEventResponse(BaseModel):
    """Response schema for analytics event rows."""

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
    def from_dto(cls, dto: AnalyticsEventResponseDTO) -> AnalyticsEventResponse:
        """Build API response from DTO."""
        return cls(**dto.model_dump())


class AnalyticsEventListResponse(BaseModel):
    """Response schema for recent analytics events."""

    items: list[AnalyticsEventResponse]
    total: int

    @classmethod
    def from_dto(cls, dto: AnalyticsEventListResponseDTO) -> AnalyticsEventListResponse:
        """Build list response from DTO."""
        return cls(
            items=[AnalyticsEventResponse.from_dto(item) for item in dto.items],
            total=dto.total,
        )


class AnalyticsOverviewResponse(BaseModel):
    """Response schema for operational metrics."""

    total_events: int
    orders_created: int
    orders_confirmed: int
    deliveries_assigned: int
    emails_sent: int
    pushes_sent: int
    notifications_sent: int
    gross_revenue: Decimal
    unique_customers: int
    date_from: datetime | None = None
    date_to: datetime | None = None

    @classmethod
    def from_dto(cls, dto: AnalyticsOverviewDTO) -> AnalyticsOverviewResponse:
        """Build overview response from DTO."""
        return cls(**dto.model_dump())
