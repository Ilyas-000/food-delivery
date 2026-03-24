"""Use case for retrieving an order by id."""

from uuid import UUID

from src.application.dto.order import OrderResponseDTO
from src.application.interfaces.order_repository import IOrderRepository
from src.domain.exceptions.order import OrderNotFoundError


class GetOrderUseCase:
    """Load order and map it to response DTO."""

    def __init__(self, repository: IOrderRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: UUID) -> OrderResponseDTO:
        """Return order response dto for existing order id."""
        order = await self._repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"order '{order_id}' not found")

        return OrderResponseDTO.from_entity(order)
