"""Repository contract for payments."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.reservation import Payment


class IPaymentRepository(ABC):
    """Persistence contract for payment aggregates."""

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        """Persist newly created payment."""

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        """Get payment by identifier."""

    @abstractmethod
    async def update(self, payment: Payment) -> Payment:
        """Persist updated payment state."""

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        """Get payment by idempotency key."""

    @abstractmethod
    async def list(
        self,
        order_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> list[Payment]:
        """List payments with optional filters."""
