"""In-memory analytics repository."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.application.dto.analytics import AnalyticsOverviewDTO
from src.application.interfaces.analytics_repository import IAnalyticsRepository
from src.domain.entities.analytics_event import AnalyticsEvent


class InMemoryAnalyticsRepository(IAnalyticsRepository):
    """Store analytics records in memory."""

    _EMAIL_SENT_EVENT = "notification-service.notification.email_sent"
    _PUSH_SENT_EVENT = "notification-service.notification.push_sent"

    def __init__(self) -> None:
        self._events: list[AnalyticsEvent] = []

    async def start(self) -> None:
        """No-op for in-memory backend."""

    async def stop(self) -> None:
        """No-op for in-memory backend."""

    def is_ready(self) -> bool:
        """Always ready in tests/dev mode."""
        return True

    async def save(self, event: AnalyticsEvent) -> AnalyticsEvent:
        """Persist event in memory."""
        self._events.append(event)
        return event

    async def list_events(
        self,
        *,
        event_type: str | None,
        limit: int,
    ) -> list[AnalyticsEvent]:
        """Return recent events filtered by type."""
        items = self._events
        if event_type:
            items = [event for event in items if event.event_type == event_type]
        return sorted(items, key=lambda event: event.occurred_at, reverse=True)[:limit]

    async def get_overview(
        self,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> AnalyticsOverviewDTO:
        """Compute overview metrics from in-memory records."""
        items = [
            event
            for event in self._events
            if (date_from is None or event.occurred_at >= date_from)
            and (date_to is None or event.occurred_at <= date_to)
        ]

        gross_revenue = sum(
            (
                event.amount
                for event in items
                if event.event_type == "order-service.order.created" and event.amount is not None
            ),
            start=Decimal("0"),
        )
        unique_customers = {
            event.user_id
            for event in items
            if event.event_type == "order-service.order.created" and event.user_id
        }

        emails_sent = sum(1 for event in items if event.event_type == self._EMAIL_SENT_EVENT)
        pushes_sent = sum(1 for event in items if event.event_type == self._PUSH_SENT_EVENT)

        return AnalyticsOverviewDTO(
            total_events=len(items),
            orders_created=sum(
                1 for event in items if event.event_type == "order-service.order.created"
            ),
            orders_confirmed=sum(
                1 for event in items if event.event_type == "order-service.order.confirmed"
            ),
            deliveries_assigned=sum(
                1 for event in items if event.event_type == "delivery-service.delivery.assigned"
            ),
            emails_sent=emails_sent,
            pushes_sent=pushes_sent,
            notifications_sent=emails_sent + pushes_sent,
            gross_revenue=gross_revenue.quantize(Decimal("0.01")),
            unique_customers=len(unique_customers),
            date_from=date_from,
            date_to=date_to,
        )

    def clear(self) -> None:
        """Reset repository state for tests."""
        self._events.clear()
