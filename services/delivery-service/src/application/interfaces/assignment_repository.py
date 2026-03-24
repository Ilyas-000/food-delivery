"""Repository contract for delivery assignments."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.assignment import DeliveryAssignment


class IAssignmentRepository(ABC):
    """Persistence contract for assignment aggregates."""

    @abstractmethod
    async def create(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Persist newly created assignment."""

    @abstractmethod
    async def get_by_id(self, assignment_id: UUID) -> DeliveryAssignment | None:
        """Get assignment by id."""

    @abstractmethod
    async def update(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Persist updated assignment."""
