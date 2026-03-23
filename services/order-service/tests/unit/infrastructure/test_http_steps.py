"""Unit tests for HTTP saga steps."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dto.order import OrderSagaContext
from src.application.interfaces.external_clients import (
    IDeliveryServiceClient,
    IPaymentServiceClient,
    IRestaurantServiceClient,
)
from src.domain.value_objects.order_item import OrderItem
from src.infrastructure.saga.http_steps import (
    AssignCourierStep,
    ReservePaymentStep,
    ValidateMenuItemsStep,
)


class StubRestaurantClient(IRestaurantServiceClient):
    """Stub restaurant client for step tests."""

    def __init__(self) -> None:
        self.called = False

    async def validate_items(self, restaurant_id: UUID, items: tuple[OrderItem, ...]) -> None:
        _ = (restaurant_id, items)
        self.called = True


class StubPaymentClient(IPaymentServiceClient):
    """Stub payment client for step tests."""

    def __init__(self) -> None:
        self.reservation_id = "res-1"
        self.released: list[str] = []

    async def reserve(
        self,
        order_id: UUID,
        user_id: UUID,
        amount: Decimal,
        currency: str,
    ) -> str:
        _ = (order_id, user_id, amount, currency)
        return self.reservation_id

    async def release(self, reservation_id: str) -> None:
        self.released.append(reservation_id)


class StubDeliveryClient(IDeliveryServiceClient):
    """Stub delivery client for step tests."""

    def __init__(self) -> None:
        self.assignment_id = "ass-1"
        self.cancelled: list[str] = []

    async def assign(self, order_id: UUID, restaurant_id: UUID) -> str:
        _ = (order_id, restaurant_id)
        return self.assignment_id

    async def cancel(self, assignment_id: str) -> None:
        self.cancelled.append(assignment_id)


def _build_context() -> OrderSagaContext:
    return OrderSagaContext(
        order_id=uuid4(),
        user_id=uuid4(),
        restaurant_id=uuid4(),
        total_amount=Decimal("250.00"),
        items=(OrderItem(menu_item_id=uuid4(), quantity=2, unit_price=Decimal("125.00")),),
    )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_validate_menu_items_step_marks_context() -> None:
    context = _build_context()
    restaurant_client = StubRestaurantClient()
    step = ValidateMenuItemsStep(restaurant_client=restaurant_client)

    await step.execute(context)
    await step.compensate(context)

    assert restaurant_client.called is True
    assert context.metadata["validate_menu_items"] == "compensated"


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_reserve_payment_step_stores_and_releases_reservation_id() -> None:
    context = _build_context()
    payment_client = StubPaymentClient()
    step = ReservePaymentStep(payment_client=payment_client)

    await step.execute(context)
    await step.compensate(context)

    assert context.metadata["payment_reservation_id"] == "res-1"
    assert payment_client.released == ["res-1"]


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_assign_courier_step_stores_and_cancels_assignment_id() -> None:
    context = _build_context()
    delivery_client = StubDeliveryClient()
    step = AssignCourierStep(delivery_client=delivery_client)

    await step.execute(context)
    await step.compensate(context)

    assert context.metadata["delivery_assignment_id"] == "ass-1"
    assert delivery_client.cancelled == ["ass-1"]
