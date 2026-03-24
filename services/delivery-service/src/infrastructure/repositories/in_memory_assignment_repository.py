"""In-memory repository for delivery assignments."""

from uuid import UUID

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.entities.assignment import DeliveryAssignment


class InMemoryAssignmentRepository(IAssignmentRepository):
    """Simple in-memory persistence for local development and tests."""

    def __init__(self) -> None:
        self._storage: dict[UUID, DeliveryAssignment] = {}

    async def create(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Store assignment."""
        self._storage[assignment.id] = assignment
        return assignment

    async def get_by_id(self, assignment_id: UUID) -> DeliveryAssignment | None:
        """Load assignment by id."""
        return self._storage.get(assignment_id)

    async def update(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Update assignment state."""
        self._storage[assignment.id] = assignment
        return assignment
