"""Unit tests for OrderItem value object."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.value_objects.order_item import OrderItem


@pytest.mark.unit()
def test_order_item_calculates_total_amount() -> None:
    item = OrderItem(menu_item_id=uuid4(), quantity=3, unit_price=Decimal("150.50"))

    assert item.total_amount == Decimal("451.50")


@pytest.mark.unit()
def test_order_item_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError, match="quantity"):
        OrderItem(menu_item_id=uuid4(), quantity=0, unit_price=Decimal("150.00"))


@pytest.mark.unit()
def test_order_item_rejects_non_positive_price() -> None:
    with pytest.raises(ValueError, match="unit_price"):
        OrderItem(menu_item_id=uuid4(), quantity=1, unit_price=Decimal("0"))
