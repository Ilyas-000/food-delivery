"""Mock saga steps for local mode (`ORDER_SERVICE_SAGA_BACKEND=mock`)."""

from src.application.dto.order import OrderSagaContext
from src.application.interfaces.saga_step import ISagaStep


class ValidateMenuItemsStep(ISagaStep):
    """Placeholder menu validation step."""

    name = "validate_menu_items"

    async def execute(self, context: OrderSagaContext) -> None:
        """Mark menu validation as completed."""
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """Mark compensation for menu validation."""
        context.metadata[self.name] = "compensated"


class ReservePaymentStep(ISagaStep):
    """Placeholder payment reservation step."""

    name = "reserve_payment"

    async def execute(self, context: OrderSagaContext) -> None:
        """Mark payment reservation as completed."""
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """Mark compensation for payment reservation."""
        context.metadata[self.name] = "compensated"


class AssignCourierStep(ISagaStep):
    """Placeholder courier assignment step."""

    name = "assign_courier"

    async def execute(self, context: OrderSagaContext) -> None:
        """Mark courier assignment as completed."""
        context.metadata[self.name] = "done"

    async def compensate(self, context: OrderSagaContext) -> None:
        """Mark compensation for courier assignment."""
        context.metadata[self.name] = "compensated"
