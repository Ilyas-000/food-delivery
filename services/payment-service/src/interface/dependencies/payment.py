"""Payment dependency providers."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.reservation_repository import IReservationRepository
from src.application.use_cases.release_payment import ReleasePaymentUseCase
from src.application.use_cases.reserve_payment import ReservePaymentUseCase
from src.infrastructure.repositories.in_memory_reservation_repository import (
    InMemoryReservationRepository,
)

_REPOSITORY = InMemoryReservationRepository()


async def get_reservation_repository() -> IReservationRepository:
    """Provide reservation repository implementation."""
    return _REPOSITORY


async def get_reserve_payment_use_case(
    repository: Annotated[IReservationRepository, Depends(get_reservation_repository)],
) -> ReservePaymentUseCase:
    """Provide reserve payment use case."""
    return ReservePaymentUseCase(repository=repository)


async def get_release_payment_use_case(
    repository: Annotated[IReservationRepository, Depends(get_reservation_repository)],
) -> ReleasePaymentUseCase:
    """Provide release payment use case."""
    return ReleasePaymentUseCase(repository=repository)
