"""Use case for recent analytics events."""

from src.application.dto.analytics import AnalyticsEventListResponseDTO, AnalyticsEventResponseDTO
from src.application.interfaces.analytics_repository import IAnalyticsRepository


class ListAnalyticsEventsUseCase:
    """Return recent analytics events."""

    def __init__(self, repository: IAnalyticsRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        event_type: str | None,
        limit: int,
    ) -> AnalyticsEventListResponseDTO:
        """Fetch recent events from repository."""
        items = await self._repository.list_events(event_type=event_type, limit=limit)
        response_items = [AnalyticsEventResponseDTO.from_entity(item) for item in items]
        return AnalyticsEventListResponseDTO(items=response_items, total=len(response_items))
