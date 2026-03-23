"""HTTP-based saga steps integrating with external services."""

from src.application.dto.order import OrderSagaContext
from src.application.interfaces.external_clients import (
    IDeliveryServiceClient,
    IPaymentServiceClient,
    IRestaurantServiceClient,
)
from src.application.interfaces.saga_step import ISagaStep


class ValidateMenuItemsStep(ISagaStep):
    """Validate menu items against restaurant service."""

    name = "validate_menu_items"

    def __init__(self, restaurant_client: IRestaurantServiceClient) -> None:
        self._restaurant_client = restaurant_client

    async def execute(self, context: OrderSagaContext) -> None:
        """Validate menu item availability and prices."""
        await self._restaurant_client.validate_items(
            restaurant_id=context.restaurant_id,
            items=context.items,
        )
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """No remote side effect for this step."""
        context.metadata[self.name] = "compensated"


class ReservePaymentStep(ISagaStep):
    """Reserve payment funds in payment service."""

    name = "reserve_payment"
    _reservation_key = "payment_reservation_id"

    def __init__(self, payment_client: IPaymentServiceClient) -> None:
        self._payment_client = payment_client

    async def execute(self, context: OrderSagaContext) -> None:
        """Reserve funds and persist reservation id in saga context."""
        reservation_id = await self._payment_client.reserve(
            order_id=context.order_id,
            user_id=context.user_id,
            amount=context.total_amount,
            currency="RUB",
        )
        context.metadata[self._reservation_key] = reservation_id
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """Release payment reservation if it exists."""
        reservation_id = context.metadata.get(self._reservation_key)
        if reservation_id is None:
            return

        await self._payment_client.release(reservation_id)
        context.metadata[self.name] = "compensated"


class AssignCourierStep(ISagaStep):
    """Assign courier through delivery service."""

    name = "assign_courier"
    _assignment_key = "delivery_assignment_id"

    def __init__(self, delivery_client: IDeliveryServiceClient) -> None:
        self._delivery_client = delivery_client

    async def execute(self, context: OrderSagaContext) -> None:
        """Assign courier and store assignment id in saga context."""
        assignment_id = await self._delivery_client.assign(
            order_id=context.order_id,
            restaurant_id=context.restaurant_id,
        )
        context.metadata[self._assignment_key] = assignment_id
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """Cancel courier assignment if it exists."""
        assignment_id = context.metadata.get(self._assignment_key)
        if assignment_id is None:
            return

        await self._delivery_client.cancel(assignment_id)
        context.metadata[self.name] = "compensated"
