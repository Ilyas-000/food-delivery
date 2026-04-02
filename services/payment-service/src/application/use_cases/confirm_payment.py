"""Confirm payment use case."""

from uuid import UUID

from src.application.dto.payment import PaymentResponseDTO
from src.application.interfaces.reservation_repository import IPaymentRepository
from src.domain.exceptions.payment import PaymentNotFoundError, PaymentStateTransitionError


class ConfirmPaymentUseCase:
    """Confirm existing pending payment."""

    def __init__(self, repository: IPaymentRepository) -> None:
        self._repository = repository

    async def execute(self, payment_id: UUID) -> PaymentResponseDTO:
        """Confirm payment by id."""
        payment = await self._repository.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(f"payment '{payment_id}' not found")

        try:
            payment.confirm()
        except ValueError as exc:
            raise PaymentStateTransitionError(str(exc)) from exc

        stored = await self._repository.update(payment)
        return PaymentResponseDTO.from_entity(stored)
