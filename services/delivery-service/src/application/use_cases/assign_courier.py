"""Assign courier use case."""

from src.application.dto.delivery import AssignCourierDTO, DeliveryAssignmentResponseDTO
from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.entities.assignment import DeliveryAssignment


class AssignCourierUseCase:
    """Create courier assignment."""

    def __init__(self, repository: IAssignmentRepository) -> None:
        self._repository = repository

    async def execute(self, dto: AssignCourierDTO) -> DeliveryAssignmentResponseDTO:
        """Assign courier for order."""
        assignment = DeliveryAssignment.create(
            order_id=dto.order_id,
            restaurant_id=dto.restaurant_id,
        )
        stored = await self._repository.create(assignment)
        return DeliveryAssignmentResponseDTO.from_entity(stored)
