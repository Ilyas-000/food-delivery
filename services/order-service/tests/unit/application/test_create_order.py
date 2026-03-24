"""Unit tests for CreateOrderUseCase saga orchestration."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dto.order import CreateOrderDTO, CreateOrderItemDTO, OrderSagaContext
from src.application.interfaces.order_repository import IOrderRepository
from src.application.interfaces.saga_step import ISagaStep
from src.application.use_cases.create_order import CreateOrderUseCase
from src.domain.entities.order import Order
from src.domain.exceptions.order import OrderSagaFailedError
from src.domain.value_objects.order_status import OrderStatus


class InMemoryOrderRepository(IOrderRepository):
    """In-memory repository used in unit tests."""

    def __init__(self) -> None:
        self.storage: dict[UUID, Order] = {}

    async def create(self, order: Order) -> Order:
        self.storage[order.id] = order
        return order

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return self.storage.get(order_id)

    async def update(self, order: Order) -> Order:
        self.storage[order.id] = order
        return order


class SpySagaStep(ISagaStep):
    """Test double for saga steps."""

    def __init__(self, name: str, fail_on_execute: bool = False) -> None:
        self.name = name
        self.fail_on_execute = fail_on_execute
        self.executed = False
        self.compensated = False

    async def execute(self, context: OrderSagaContext) -> None:
        self.executed = True
        context.metadata[self.name] = "done"
        if self.fail_on_execute:
            raise RuntimeError(f"{self.name} failed")

    async def compensate(self, context: OrderSagaContext) -> None:
        self.compensated = True
        context.metadata[self.name] = "compensated"


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_order_happy_path_confirms_order() -> None:
    repository = InMemoryOrderRepository()
    steps = [SpySagaStep("validate_menu"), SpySagaStep("reserve_payment")]
    use_case = CreateOrderUseCase(repository=repository, saga_steps=steps)

    dto = CreateOrderDTO(
        user_id=uuid4(),
        restaurant_id=uuid4(),
        items=[
            CreateOrderItemDTO(menu_item_id=uuid4(), quantity=2, unit_price=Decimal("100.00")),
        ],
    )

    result = await use_case.execute(dto)

    assert result.status == OrderStatus.CONFIRMED
    assert all(step.executed for step in steps)
    assert not any(step.compensated for step in steps)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_create_order_runs_compensation_on_failure() -> None:
    repository = InMemoryOrderRepository()
    step_one = SpySagaStep("validate_menu")
    step_two = SpySagaStep("reserve_payment", fail_on_execute=True)
    use_case = CreateOrderUseCase(repository=repository, saga_steps=[step_one, step_two])

    dto = CreateOrderDTO(
        user_id=uuid4(),
        restaurant_id=uuid4(),
        items=[CreateOrderItemDTO(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("50.00"))],
    )

    with pytest.raises(OrderSagaFailedError, match="reserve_payment"):
        await use_case.execute(dto)

    stored_order = next(iter(repository.storage.values()))
    assert stored_order.status == OrderStatus.CANCELLED
    assert step_one.executed is True
    assert step_one.compensated is True
    assert step_two.compensated is False
