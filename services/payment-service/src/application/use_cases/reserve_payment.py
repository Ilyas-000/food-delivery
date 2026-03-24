"""Reserve payment use case."""

from src.application.dto.payment import (
    PaymentReservationResponseDTO,
    ReservePaymentDTO,
)
from src.application.interfaces.reservation_repository import IReservationRepository
from src.domain.entities.reservation import PaymentReservation


class ReservePaymentUseCase:
    """Create payment reservation."""

    def __init__(self, repository: IReservationRepository) -> None:
        self._repository = repository

    async def execute(self, dto: ReservePaymentDTO) -> PaymentReservationResponseDTO:
        """Reserve funds for order."""
        reservation = PaymentReservation.create(
            order_id=dto.order_id,
            user_id=dto.user_id,
            amount=dto.amount,
            currency=dto.currency,
        )
        stored = await self._repository.create(reservation)
        return PaymentReservationResponseDTO.from_entity(stored)
