"""Contract for selecting courier identity during assignment."""

from abc import ABC, abstractmethod
from uuid import UUID


class ICourierAllocator(ABC):
    """Select courier identity for a new delivery assignment."""

    @abstractmethod
    def allocate(self) -> UUID:
        """Return courier id for the next assignment."""
