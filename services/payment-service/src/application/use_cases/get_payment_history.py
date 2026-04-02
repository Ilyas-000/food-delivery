"""Get payment history use case."""

from uuid import UUID

from src.application.dto.payment import PaymentHistoryResponseDTO, PaymentResponseDTO
from src.application.interfaces.reservation_repository import IPaymentRepository


class GetPaymentHistoryUseCase:
    """Read payment history with optional filters."""

    def __init__(self, repository: IPaymentRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        order_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> PaymentHistoryResponseDTO:
        """Get payment history."""
        payments = await self._repository.list(order_id=order_id, user_id=user_id)
        items = [PaymentResponseDTO.from_entity(payment) for payment in payments]
        return PaymentHistoryResponseDTO(items=items, total=len(items))
