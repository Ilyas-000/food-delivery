"""Repository contract for orders."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.order import Order


class IOrderRepository(ABC):
    """Persistence boundary for order aggregate."""

    @abstractmethod
    async def create(self, order: Order) -> Order:
        """Persist a new order."""

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        """Load order by id."""

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Persist order state changes."""
