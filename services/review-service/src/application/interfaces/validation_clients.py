"""External validation client contracts."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.application.dto.review import DeliverySnapshotDTO, OrderSnapshotDTO


class IOrderValidationClient(ABC):
    """Read order state from order-service."""

    @abstractmethod
    async def get_order(self, order_id: UUID) -> OrderSnapshotDTO:
        """Fetch order snapshot."""


class IDeliveryValidationClient(ABC):
    """Read delivery state from delivery-service."""

    @abstractmethod
    async def get_delivery(self, order_id: UUID) -> DeliverySnapshotDTO:
        """Fetch delivery snapshot."""
