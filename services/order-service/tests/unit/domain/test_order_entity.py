"""Unit tests for Order aggregate."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.order import Order
from src.domain.exceptions.order import InvalidOrderDataError, InvalidOrderTransitionError
from src.domain.value_objects.order_item import OrderItem
from src.domain.value_objects.order_status import OrderStatus


@pytest.mark.unit()
def test_create_order_sets_pending_status_and_total_amount() -> None:
    items = [
        OrderItem(menu_item_id=uuid4(), quantity=2, unit_price=Decimal("200.00")),
        OrderItem(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("100.50")),
    ]

    order = Order.create(user_id=uuid4(), restaurant_id=uuid4(), items=items)

    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("500.50")


@pytest.mark.unit()
def test_create_order_requires_items() -> None:
    with pytest.raises(InvalidOrderDataError, match="at least one item"):
        Order.create(user_id=uuid4(), restaurant_id=uuid4(), items=[])


@pytest.mark.unit()
def test_order_happy_path_transitions() -> None:
    items = [OrderItem(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("250.00"))]
    order = Order.create(user_id=uuid4(), restaurant_id=uuid4(), items=items)

    order.confirm()
    order.start_preparing()
    order.mark_ready()
    order.start_delivery()
    order.mark_delivered()

    assert order.status == OrderStatus.DELIVERED


@pytest.mark.unit()
def test_order_rejects_invalid_transition() -> None:
    items = [OrderItem(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("250.00"))]
    order = Order.create(user_id=uuid4(), restaurant_id=uuid4(), items=items)

    with pytest.raises(InvalidOrderTransitionError, match="cannot transition"):
        order.mark_delivered()


@pytest.mark.unit()
def test_order_can_be_cancelled_before_delivery() -> None:
    items = [OrderItem(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("250.00"))]
    order = Order.create(user_id=uuid4(), restaurant_id=uuid4(), items=items)

    order.cancel("payment_rejected")

    assert order.status == OrderStatus.CANCELLED
    assert order.cancellation_reason == "payment_rejected"
