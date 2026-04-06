"""Unit tests for analytics event domain entity."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.analytics_event import AnalyticsEvent
from src.domain.exceptions.analytics import AnalyticsValidationError


@pytest.mark.unit()
def test_analytics_event_requires_non_empty_event_type() -> None:
    with pytest.raises(AnalyticsValidationError, match="event_type"):
        AnalyticsEvent.create(
            event_id=uuid4(),
            event_type="   ",
            aggregate_id="order-1",
            aggregate_type="order",
            occurred_at=datetime(2026, 4, 6, 12, 0, tzinfo=UTC),
        )


@pytest.mark.unit()
def test_analytics_event_requires_timezone_aware_occurred_at() -> None:
    with pytest.raises(AnalyticsValidationError, match="timezone-aware"):
        AnalyticsEvent.create(
            event_id=uuid4(),
            event_type="order-service.order.created",
            aggregate_id="order-1",
            aggregate_type="order",
            occurred_at=datetime(2026, 4, 6, 12, 0, tzinfo=UTC).replace(tzinfo=None),
        )
