"""Complete delivery use case."""

from uuid import UUID

from src.application.dto.delivery import DeliveryAssignmentResponseDTO
from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.exceptions.delivery import (
    DeliveryAssignmentNotFoundError,
    DeliveryInvalidStateError,
)


class CompleteDeliveryUseCase:
    """Complete delivery by order id."""

    def __init__(self, repository: IAssignmentRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: UUID) -> DeliveryAssignmentResponseDTO:
        """Mark delivery assignment as completed."""
        assignment = await self._repository.get_by_order_id(order_id)
        if assignment is None:
            raise DeliveryAssignmentNotFoundError(f"assignment for order '{order_id}' not found")

        try:
            assignment.complete()
        except ValueError as exc:
            raise DeliveryInvalidStateError(str(exc)) from exc

        updated = await self._repository.update(assignment)
        return DeliveryAssignmentResponseDTO.from_entity(updated)
