"""In-memory repository for payments."""

from uuid import UUID

from src.application.interfaces.reservation_repository import IPaymentRepository
from src.domain.entities.reservation import Payment


class InMemoryReservationRepository(IPaymentRepository):
    """Simple in-memory persistence for local development and tests."""

    def __init__(self) -> None:
        self._storage: dict[UUID, Payment] = {}
        self._idempotency_index: dict[str, UUID] = {}

    async def create(self, payment: Payment) -> Payment:
        """Store payment."""
        self._storage[payment.id] = payment
        if payment.idempotency_key is not None:
            self._idempotency_index[payment.idempotency_key] = payment.id
        return payment

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        """Load payment by id."""
        return self._storage.get(payment_id)

    async def update(self, payment: Payment) -> Payment:
        """Update payment state."""
        self._storage[payment.id] = payment
        if payment.idempotency_key is not None:
            self._idempotency_index[payment.idempotency_key] = payment.id
        return payment

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        """Find payment by idempotency key."""
        payment_id = self._idempotency_index.get(idempotency_key)
        if payment_id is None:
            return None
        return self._storage.get(payment_id)

    async def list(
        self,
        order_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> list[Payment]:
        """List payments with optional order and user filters."""
        items = [
            payment
            for payment in self._storage.values()
            if (order_id is None or payment.order_id == order_id)
            and (user_id is None or payment.user_id == user_id)
        ]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def clear(self) -> None:
        """Clear in-memory state for test isolation."""
        self._storage.clear()
        self._idempotency_index.clear()
