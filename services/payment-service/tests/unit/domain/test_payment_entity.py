"""Unit tests for payment entity transitions."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.reservation import Payment, PaymentStatus
from src.domain.value_objects.money import Money


def _create_payment() -> Payment:
    return Payment.create(
        order_id=uuid4(),
        user_id=uuid4(),
        money=Money(amount=Decimal("250.00"), currency="RUB"),
        idempotency_key=str(uuid4()),
    )


@pytest.mark.unit()
def test_payment_create_sets_pending_status() -> None:
    payment = _create_payment()

    assert payment.status == PaymentStatus.PENDING
    assert payment.amount == Decimal("250.00")
    assert payment.currency == "RUB"


@pytest.mark.unit()
def test_payment_confirm_transition_from_pending() -> None:
    payment = _create_payment()

    payment.confirm()

    assert payment.status == PaymentStatus.COMPLETED


@pytest.mark.unit()
def test_payment_release_transition_from_pending() -> None:
    payment = _create_payment()

    payment.release()

    assert payment.status == PaymentStatus.FAILED


@pytest.mark.unit()
def test_payment_refund_transition_from_completed() -> None:
    payment = _create_payment()
    payment.confirm()

    payment.refund()

    assert payment.status == PaymentStatus.REFUNDED


@pytest.mark.unit()
def test_payment_rejects_confirm_after_release() -> None:
    payment = _create_payment()
    payment.release()

    with pytest.raises(ValueError, match="cannot confirm"):
        payment.confirm()


@pytest.mark.unit()
def test_payment_rejects_refund_from_pending() -> None:
    payment = _create_payment()

    with pytest.raises(ValueError, match="cannot refund"):
        payment.refund()
