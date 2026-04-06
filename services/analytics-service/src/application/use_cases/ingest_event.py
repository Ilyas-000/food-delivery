"""Use case for analytics event ingestion."""

from src.application.dto.analytics import AnalyticsEventResponseDTO, IngestAnalyticsEventDTO
from src.application.interfaces.analytics_repository import IAnalyticsRepository
from src.domain.entities.analytics_event import AnalyticsEvent


class IngestAnalyticsEventUseCase:
    """Persist normalized analytics events."""

    def __init__(self, repository: IAnalyticsRepository) -> None:
        self._repository = repository

    async def execute(self, dto: IngestAnalyticsEventDTO) -> AnalyticsEventResponseDTO:
        """Validate and store analytics event."""
        event = AnalyticsEvent.create(
            event_id=dto.event_id,
            event_type=dto.event_type,
            aggregate_id=dto.aggregate_id,
            aggregate_type=dto.aggregate_type,
            occurred_at=dto.occurred_at,
            user_id=dto.user_id,
            order_id=dto.order_id,
            restaurant_id=dto.restaurant_id,
            amount=dto.amount,
            currency=dto.currency,
            notification_type=dto.notification_type,
            recipient=dto.recipient,
            template_name=dto.template_name,
            source_event_type=dto.source_event_type,
            payload=dto.payload,
        )
        stored = await self._repository.save(event)
        return AnalyticsEventResponseDTO.from_entity(stored)
