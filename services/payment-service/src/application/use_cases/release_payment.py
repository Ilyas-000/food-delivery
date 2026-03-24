"""Release payment reservation use case."""

from uuid import UUID

from src.application.interfaces.reservation_repository import IReservationRepository
from src.domain.exceptions.payment import PaymentReservationNotFoundError


class ReleasePaymentUseCase:
    """Release existing payment reservation."""

    def __init__(self, repository: IReservationRepository) -> None:
        self._repository = repository

    async def execute(self, reservation_id: UUID) -> None:
        """Release reservation by id."""
        reservation = await self._repository.get_by_id(reservation_id)
        if reservation is None:
            raise PaymentReservationNotFoundError(f"reservation '{reservation_id}' not found")

        reservation.release()
        await self._repository.update(reservation)
