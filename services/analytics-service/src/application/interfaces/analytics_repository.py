"""Analytics repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.application.dto.analytics import AnalyticsOverviewDTO
from src.domain.entities.analytics_event import AnalyticsEvent


class IAnalyticsRepository(ABC):
    """Analytics storage abstraction."""

    @abstractmethod
    async def start(self) -> None:
        """Initialize repository resources."""

    @abstractmethod
    async def stop(self) -> None:
        """Release repository resources."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Return readiness state."""

    @abstractmethod
    async def save(self, event: AnalyticsEvent) -> AnalyticsEvent:
        """Persist analytics event."""

    @abstractmethod
    async def list_events(
        self,
        *,
        event_type: str | None,
        limit: int,
    ) -> list[AnalyticsEvent]:
        """Return recent analytics events."""

    @abstractmethod
    async def get_overview(
        self,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> AnalyticsOverviewDTO:
        """Return aggregated operational metrics."""
