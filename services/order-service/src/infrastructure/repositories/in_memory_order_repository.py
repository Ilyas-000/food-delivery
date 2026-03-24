"""In-memory repository for local development and tests."""

from uuid import UUID

from src.application.interfaces.order_repository import IOrderRepository
from src.domain.entities.order import Order


class InMemoryOrderRepository(IOrderRepository):
    """Simple repository implementation backed by in-process dict."""

    def __init__(self) -> None:
        self._storage: dict[UUID, Order] = {}

    async def create(self, order: Order) -> Order:
        """Persist new order in memory."""
        self._storage[order.id] = order
        return order

    async def get_by_id(self, order_id: UUID) -> Order | None:
        """Fetch order by id from memory."""
        return self._storage.get(order_id)

    async def update(self, order: Order) -> Order:
        """Update existing order state in memory."""
        self._storage[order.id] = order
        return order
