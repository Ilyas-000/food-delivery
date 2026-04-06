"""Contracts for delivery domain event publishing."""

from abc import ABC, abstractmethod

from src.domain.entities.assignment import DeliveryAssignment


class IDeliveryEventPublisher(ABC):
    """Delivery event publisher contract."""

    @abstractmethod
    async def publish_assignment_created(self, assignment: DeliveryAssignment) -> None:
        """Publish assignment created event."""
