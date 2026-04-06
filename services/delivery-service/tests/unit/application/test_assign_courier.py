"""Unit tests for assign courier use case."""

from uuid import UUID, uuid4

import pytest

from src.application.dto.delivery import AssignCourierDTO
from src.application.interfaces.courier_allocator import ICourierAllocator
from src.application.interfaces.event_publisher import IDeliveryEventPublisher
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.domain.entities.assignment import DeliveryAssignment
from src.infrastructure.repositories.in_memory_assignment_repository import (
    InMemoryAssignmentRepository,
)


class SpyDeliveryEventPublisher(IDeliveryEventPublisher):
    """Test double for delivery event publishing."""

    def __init__(self) -> None:
        self.assignment_ids: list[UUID] = []

    async def publish_assignment_created(self, assignment: DeliveryAssignment) -> None:
        self.assignment_ids.append(assignment.id)


class StubCourierAllocator(ICourierAllocator):
    """Deterministic courier allocator for tests."""

    def __init__(self, courier_id: UUID) -> None:
        self._courier_id = courier_id

    def allocate(self) -> UUID:
        """Return configured courier id."""
        return self._courier_id


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_assign_courier_use_case_publishes_assignment_event() -> None:
    repository = InMemoryAssignmentRepository()
    event_publisher = SpyDeliveryEventPublisher()
    courier_id = uuid4()
    use_case = AssignCourierUseCase(
        repository=repository,
        event_publisher=event_publisher,
        courier_allocator=StubCourierAllocator(courier_id),
    )

    result = await use_case.execute(
        AssignCourierDTO(
            order_id=uuid4(),
            restaurant_id=uuid4(),
        )
    )

    assert len(event_publisher.assignment_ids) == 1
    assert event_publisher.assignment_ids[0] == result.id
    assert result.courier_id == courier_id
