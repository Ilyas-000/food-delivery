"""Use case for analytics overview."""

from __future__ import annotations

from datetime import datetime

from src.application.dto.analytics import AnalyticsOverviewDTO
from src.application.interfaces.analytics_repository import IAnalyticsRepository
from src.domain.exceptions.analytics import AnalyticsValidationError


class GetAnalyticsOverviewUseCase:
    """Return aggregated operational metrics."""

    def __init__(self, repository: IAnalyticsRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> AnalyticsOverviewDTO:
        """Fetch overview metrics for an optional time window."""
        if date_from and date_to and date_from > date_to:
            msg = "date_from must be less than or equal to date_to"
            raise AnalyticsValidationError(msg)
        return await self._repository.get_overview(date_from=date_from, date_to=date_to)
