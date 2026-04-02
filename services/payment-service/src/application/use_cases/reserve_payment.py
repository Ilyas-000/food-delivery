"""Reserve payment use case."""

from src.application.dto.payment import (
    PaymentResponseDTO,
    ReservePaymentDTO,
)
from src.application.interfaces.reservation_repository import IPaymentRepository
from src.domain.entities.reservation import Payment
from src.domain.exceptions.payment import (
    PaymentIdempotencyConflictError,
    PaymentValidationError,
)
from src.domain.value_objects.money import Money


class ReservePaymentUseCase:
    """Create payment reservation."""

    def __init__(self, repository: IPaymentRepository) -> None:
        self._repository = repository

    async def execute(self, dto: ReservePaymentDTO) -> PaymentResponseDTO:
        """Reserve funds for order."""
        try:
            money = Money(amount=dto.amount, currency=dto.currency)
        except ValueError as exc:
            raise PaymentValidationError(str(exc)) from exc

        if dto.idempotency_key is not None:
            existing_payment = await self._repository.get_by_idempotency_key(dto.idempotency_key)
            if existing_payment is not None:
                if existing_payment.matches_request(
                    order_id=dto.order_id,
                    user_id=dto.user_id,
                    money=money,
                ):
                    return PaymentResponseDTO.from_entity(existing_payment)
                raise PaymentIdempotencyConflictError(
                    f"idempotency key '{dto.idempotency_key}' already used with different payload"
                )

        payment = Payment.create(
            order_id=dto.order_id,
            user_id=dto.user_id,
            money=money,
            idempotency_key=dto.idempotency_key,
        )
        stored = await self._repository.create(payment)
        return PaymentResponseDTO.from_entity(stored)
