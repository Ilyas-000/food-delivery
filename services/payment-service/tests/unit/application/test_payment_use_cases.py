"""Unit tests for payment application use cases."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dto.payment import ReservePaymentDTO
from src.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from src.application.use_cases.get_payment import GetPaymentUseCase
from src.application.use_cases.get_payment_history import GetPaymentHistoryUseCase
from src.application.use_cases.refund_payment import RefundPaymentUseCase
from src.application.use_cases.release_payment import ReleasePaymentUseCase
from src.application.use_cases.reserve_payment import ReservePaymentUseCase
from src.domain.exceptions.payment import (
    PaymentIdempotencyConflictError,
    PaymentNotFoundError,
    PaymentStateTransitionError,
    PaymentValidationError,
)
from src.infrastructure.repositories.in_memory_reservation_repository import (
    InMemoryReservationRepository,
)


def _reserve_dto(
    order_id: UUID | None = None,
    user_id: UUID | None = None,
    amount: str = "120.00",
    currency: str = "RUB",
    idempotency_key: str | None = None,
) -> ReservePaymentDTO:
    return ReservePaymentDTO(
        order_id=uuid4() if order_id is None else order_id,
        user_id=uuid4() if user_id is None else user_id,
        amount=Decimal(amount),
        currency=currency,
        idempotency_key=idempotency_key,
    )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_reserve_use_case_validates_money() -> None:
    repository = InMemoryReservationRepository()
    use_case = ReservePaymentUseCase(repository)

    with pytest.raises(PaymentValidationError, match="greater than zero"):
        await use_case.execute(_reserve_dto(amount="0"))


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_reserve_use_case_returns_same_payment_for_same_idempotency_payload() -> None:
    repository = InMemoryReservationRepository()
    use_case = ReservePaymentUseCase(repository)

    order_id = uuid4()
    user_id = uuid4()
    key = str(uuid4())
    dto = ReservePaymentDTO(
        order_id=order_id,
        user_id=user_id,
        amount=Decimal("120.00"),
        currency="RUB",
        idempotency_key=key,
    )

    first = await use_case.execute(dto)
    second = await use_case.execute(dto)

    assert first.id == second.id


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_reserve_use_case_raises_conflict_for_different_payload_with_same_key() -> None:
    repository = InMemoryReservationRepository()
    use_case = ReservePaymentUseCase(repository)

    order_id = uuid4()
    user_id = uuid4()
    key = str(uuid4())
    await use_case.execute(
        ReservePaymentDTO(
            order_id=order_id,
            user_id=user_id,
            amount=Decimal("120.00"),
            currency="RUB",
            idempotency_key=key,
        )
    )

    with pytest.raises(PaymentIdempotencyConflictError, match="already used"):
        await use_case.execute(
            ReservePaymentDTO(
                order_id=order_id,
                user_id=user_id,
                amount=Decimal("121.00"),
                currency="RUB",
                idempotency_key=key,
            )
        )


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_confirm_use_case_raises_not_found() -> None:
    repository = InMemoryReservationRepository()
    use_case = ConfirmPaymentUseCase(repository)

    with pytest.raises(PaymentNotFoundError, match="not found"):
        await use_case.execute(uuid4())


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_refund_use_case_requires_completed_status() -> None:
    repository = InMemoryReservationRepository()
    reserve = ReservePaymentUseCase(repository)
    refund = RefundPaymentUseCase(repository)

    payment = await reserve.execute(_reserve_dto())

    with pytest.raises(PaymentStateTransitionError, match="cannot refund"):
        await refund.execute(payment.id)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_release_then_confirm_raises_state_transition_error() -> None:
    repository = InMemoryReservationRepository()
    reserve = ReservePaymentUseCase(repository)
    release = ReleasePaymentUseCase(repository)
    confirm = ConfirmPaymentUseCase(repository)

    payment = await reserve.execute(_reserve_dto())
    await release.execute(payment.id)

    with pytest.raises(PaymentStateTransitionError, match="cannot confirm"):
        await confirm.execute(payment.id)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_payment_and_history_use_cases_with_user_filter() -> None:
    repository = InMemoryReservationRepository()
    reserve = ReservePaymentUseCase(repository)
    get_payment = GetPaymentUseCase(repository)
    history = GetPaymentHistoryUseCase(repository)

    target_user_id = uuid4()
    first = await reserve.execute(
        ReservePaymentDTO(
            order_id=uuid4(),
            user_id=target_user_id,
            amount=Decimal("100.00"),
            currency="RUB",
        )
    )
    await reserve.execute(_reserve_dto())

    payment = await get_payment.execute(first.id)
    user_history = await history.execute(user_id=target_user_id)

    assert payment.id == first.id
    assert user_history.total == 1
    assert user_history.items[0].id == first.id
