"""Round-robin courier allocator for local dispatch simulation."""

from collections import deque
from uuid import UUID

from src.application.interfaces.courier_allocator import ICourierAllocator


class RoundRobinCourierAllocator(ICourierAllocator):
    """Rotate through configured courier identities."""

    def __init__(self, courier_ids: tuple[UUID, ...]) -> None:
        if not courier_ids:
            raise ValueError("at least one courier id must be configured")
        self._courier_ids = deque(courier_ids)

    def allocate(self) -> UUID:
        """Return next courier id and move it to the end of the pool."""
        courier_id = self._courier_ids[0]
        self._courier_ids.rotate(-1)
        return courier_id
