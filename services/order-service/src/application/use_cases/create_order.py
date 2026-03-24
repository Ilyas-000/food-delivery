"""Create order saga orchestrator."""

from collections.abc import Sequence

import structlog

from src.application.dto.order import CreateOrderDTO, OrderResponseDTO, OrderSagaContext
from src.application.interfaces.order_repository import IOrderRepository
from src.application.interfaces.saga_step import ISagaStep
from src.domain.entities.order import Order
from src.domain.exceptions.order import OrderSagaFailedError
from src.domain.value_objects.order_item import OrderItem

logger = structlog.get_logger(__name__)


class CreateOrderUseCase:
    """Orchestrates order creation through saga steps."""

    def __init__(self, repository: IOrderRepository, saga_steps: Sequence[ISagaStep]) -> None:
        self._repository = repository
        self._saga_steps = tuple(saga_steps)

    async def execute(self, dto: CreateOrderDTO) -> OrderResponseDTO:
        """Create order, run saga, and return final order state."""
        items = [
            OrderItem(
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
            )
            for item in dto.items
        ]

        order = Order.create(
            user_id=dto.user_id,
            restaurant_id=dto.restaurant_id,
            items=items,
        )
        stored_order = await self._repository.create(order)

        context = OrderSagaContext(
            order_id=stored_order.id,
            user_id=stored_order.user_id,
            restaurant_id=stored_order.restaurant_id,
            total_amount=stored_order.total_amount,
            items=stored_order.items,
        )

        completed_steps: list[ISagaStep] = []
        failed_step_name = "unknown"

        try:
            for step in self._saga_steps:
                failed_step_name = step.name
                await step.execute(context)
                completed_steps.append(step)
        except Exception as error:
            for step in reversed(completed_steps):
                try:
                    await step.compensate(context)
                except Exception:
                    logger.exception(
                        "order_saga.compensation_failed",
                        order_id=str(stored_order.id),
                        step_name=step.name,
                    )

            stored_order.cancel("saga_failed")
            await self._repository.update(stored_order)

            raise OrderSagaFailedError(
                f"order saga failed at step '{failed_step_name}': {error}"
            ) from error

        stored_order.confirm()
        updated_order = await self._repository.update(stored_order)
        return OrderResponseDTO.from_entity(updated_order)
