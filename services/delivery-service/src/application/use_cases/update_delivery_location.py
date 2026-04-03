"""Update delivery location use case."""

from src.application.dto.delivery import DeliveryAssignmentResponseDTO, UpdateDeliveryLocationDTO
from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.exceptions.delivery import (
    DeliveryAssignmentNotFoundError,
    DeliveryInvalidStateError,
)
from src.domain.value_objects.location import Location


class UpdateDeliveryLocationUseCase:
    """Update current location for delivery assignment."""

    def __init__(self, repository: IAssignmentRepository) -> None:
        self._repository = repository

    async def execute(self, dto: UpdateDeliveryLocationDTO) -> DeliveryAssignmentResponseDTO:
        """Update location by order id."""
        assignment = await self._repository.get_by_order_id(dto.order_id)
        if assignment is None:
            raise DeliveryAssignmentNotFoundError(
                f"assignment for order '{dto.order_id}' not found"
            )

        try:
            location = Location(latitude=dto.latitude, longitude=dto.longitude)
            assignment.update_location(location)
        except ValueError as exc:
            raise DeliveryInvalidStateError(str(exc)) from exc

        updated = await self._repository.update(assignment)
        return DeliveryAssignmentResponseDTO.from_entity(updated)
