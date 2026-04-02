"""Get payment details use case."""

from uuid import UUID

from src.application.dto.payment import PaymentResponseDTO
from src.application.interfaces.reservation_repository import IPaymentRepository
from src.domain.exceptions.payment import PaymentNotFoundError


class GetPaymentUseCase:
    """Read payment by identifier."""

    def __init__(self, repository: IPaymentRepository) -> None:
        self._repository = repository

    async def execute(self, payment_id: UUID) -> PaymentResponseDTO:
        """Get payment by id."""
        payment = await self._repository.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(f"payment '{payment_id}' not found")
        return PaymentResponseDTO.from_entity(payment)
