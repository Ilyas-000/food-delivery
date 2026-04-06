"""Analytics event domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.domain.exceptions.analytics import AnalyticsValidationError


@dataclass(slots=True)
class AnalyticsEvent:
    """Normalized analytics record."""

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
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        event_id: UUID,
        event_type: str,
        aggregate_id: str,
        aggregate_type: str,
        occurred_at: datetime,
        user_id: str | None = None,
        order_id: str | None = None,
        restaurant_id: str | None = None,
        amount: Decimal | None = None,
        currency: str | None = None,
        notification_type: str | None = None,
        recipient: str | None = None,
        template_name: str | None = None,
        source_event_type: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AnalyticsEvent:
        """Create analytics event with basic invariants."""
        normalized_event_type = event_type.strip()
        normalized_aggregate_id = aggregate_id.strip()
        normalized_aggregate_type = aggregate_type.strip()

        if not normalized_event_type:
            msg = "event_type must not be empty"
            raise AnalyticsValidationError(msg)
        if not normalized_aggregate_id:
            msg = "aggregate_id must not be empty"
            raise AnalyticsValidationError(msg)
        if not normalized_aggregate_type:
            msg = "aggregate_type must not be empty"
            raise AnalyticsValidationError(msg)
        if occurred_at.tzinfo is None:
            msg = "occurred_at must be timezone-aware"
            raise AnalyticsValidationError(msg)

        return cls(
            event_id=event_id,
            event_type=normalized_event_type,
            aggregate_id=normalized_aggregate_id,
            aggregate_type=normalized_aggregate_type,
            occurred_at=occurred_at.astimezone(UTC),
            user_id=user_id.strip() if user_id else None,
            order_id=order_id.strip() if order_id else None,
            restaurant_id=restaurant_id.strip() if restaurant_id else None,
            amount=amount,
            currency=currency.strip().upper() if currency else None,
            notification_type=notification_type.strip() if notification_type else None,
            recipient=recipient.strip() if recipient else None,
            template_name=template_name.strip() if template_name else None,
            source_event_type=source_event_type.strip() if source_event_type else None,
            payload=payload or {},
        )
