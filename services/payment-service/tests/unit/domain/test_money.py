"""Unit tests for Money value object."""

from decimal import Decimal

import pytest

from src.domain.value_objects.money import Money


@pytest.mark.unit()
def test_money_normalizes_amount_and_currency() -> None:
    money = Money(amount=Decimal("100.555"), currency=" rub ")

    assert money.amount == Decimal("100.56")
    assert money.currency == "RUB"


@pytest.mark.unit()
def test_money_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        Money(amount=Decimal("0"), currency="RUB")


@pytest.mark.unit()
def test_money_rejects_invalid_currency_code() -> None:
    with pytest.raises(ValueError, match="3-letter"):
        Money(amount=Decimal("10"), currency="R1")
