"""Payment dependency providers."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.reservation_repository import IPaymentRepository
from src.application.use_cases.confirm_payment import ConfirmPaymentUseCase
from src.application.use_cases.get_payment import GetPaymentUseCase
from src.application.use_cases.get_payment_history import GetPaymentHistoryUseCase
from src.application.use_cases.refund_payment import RefundPaymentUseCase
from src.application.use_cases.release_payment import ReleasePaymentUseCase
from src.application.use_cases.reserve_payment import ReservePaymentUseCase
from src.infrastructure.repositories.in_memory_reservation_repository import (
    InMemoryReservationRepository,
)

_REPOSITORY = InMemoryReservationRepository()


async def get_reservation_repository() -> IPaymentRepository:
    """Provide reservation repository implementation."""
    return _REPOSITORY


def reset_payment_repository() -> None:
    """Reset repository state for tests."""
    _REPOSITORY.clear()


async def get_reserve_payment_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> ReservePaymentUseCase:
    """Provide reserve payment use case."""
    return ReservePaymentUseCase(repository=repository)


async def get_release_payment_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> ReleasePaymentUseCase:
    """Provide release payment use case."""
    return ReleasePaymentUseCase(repository=repository)


async def get_confirm_payment_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> ConfirmPaymentUseCase:
    """Provide confirm payment use case."""
    return ConfirmPaymentUseCase(repository=repository)


async def get_refund_payment_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> RefundPaymentUseCase:
    """Provide refund payment use case."""
    return RefundPaymentUseCase(repository=repository)


async def get_payment_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> GetPaymentUseCase:
    """Provide get payment use case."""
    return GetPaymentUseCase(repository=repository)


async def get_payment_history_use_case(
    repository: Annotated[IPaymentRepository, Depends(get_reservation_repository)],
) -> GetPaymentHistoryUseCase:
    """Provide payment history use case."""
    return GetPaymentHistoryUseCase(repository=repository)
