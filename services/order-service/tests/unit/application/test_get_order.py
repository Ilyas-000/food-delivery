"""Unit tests for GetOrderUseCase."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.interfaces.order_repository import IOrderRepository
from src.application.use_cases.get_order import GetOrderUseCase
from src.domain.entities.order import Order
from src.domain.exceptions.order import OrderNotFoundError
from src.domain.value_objects.order_item import OrderItem


class InMemoryOrderRepository(IOrderRepository):
    """In-memory repository for use case tests."""

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


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_order_returns_order() -> None:
    repository = InMemoryOrderRepository()
    order = Order.create(
        user_id=uuid4(),
        restaurant_id=uuid4(),
        items=[OrderItem(menu_item_id=uuid4(), quantity=2, unit_price=Decimal("199.99"))],
    )
    await repository.create(order)

    use_case = GetOrderUseCase(repository)
    result = await use_case.execute(order.id)

    assert result.id == order.id
    assert result.total_amount == Decimal("399.98")


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_order_raises_not_found() -> None:
    repository = InMemoryOrderRepository()
    use_case = GetOrderUseCase(repository)

    with pytest.raises(OrderNotFoundError, match="not found"):
        await use_case.execute(uuid4())
