"""Cancel assignment use case."""

from uuid import UUID

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.exceptions.delivery import DeliveryAssignmentNotFoundError


class CancelAssignmentUseCase:
    """Cancel existing assignment."""

    def __init__(self, repository: IAssignmentRepository) -> None:
        self._repository = repository

    async def execute(self, assignment_id: UUID) -> None:
        """Cancel assignment by id."""
        assignment = await self._repository.get_by_id(assignment_id)
        if assignment is None:
            raise DeliveryAssignmentNotFoundError(f"assignment '{assignment_id}' not found")

        assignment.cancel()
        await self._repository.update(assignment)
