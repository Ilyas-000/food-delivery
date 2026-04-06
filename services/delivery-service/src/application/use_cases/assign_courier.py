"""Assign courier use case."""

import structlog

from src.application.dto.delivery import AssignCourierDTO, DeliveryAssignmentResponseDTO
from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.application.interfaces.event_publisher import IDeliveryEventPublisher
from src.domain.entities.assignment import DeliveryAssignment

logger = structlog.get_logger(__name__)


class AssignCourierUseCase:
    """Create courier assignment."""

    def __init__(
        self,
        repository: IAssignmentRepository,
        event_publisher: IDeliveryEventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(self, dto: AssignCourierDTO) -> DeliveryAssignmentResponseDTO:
        """Assign courier for order."""
        assignment = DeliveryAssignment.create(
            order_id=dto.order_id,
            restaurant_id=dto.restaurant_id,
        )
        stored = await self._repository.create(assignment)
        try:
            await self._event_publisher.publish_assignment_created(stored)
        except Exception:
            logger.exception(
                "delivery.events.publish_assignment_created_failed",
                assignment_id=str(stored.id),
            )
        return DeliveryAssignmentResponseDTO.from_entity(stored)
