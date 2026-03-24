"""Repository contract for payment reservations."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.reservation import PaymentReservation


class IReservationRepository(ABC):
    """Persistence contract for reservation aggregates."""

    @abstractmethod
    async def create(self, reservation: PaymentReservation) -> PaymentReservation:
        """Persist newly created reservation."""

    @abstractmethod
    async def get_by_id(self, reservation_id: UUID) -> PaymentReservation | None:
        """Get reservation by identifier."""

    @abstractmethod
    async def update(self, reservation: PaymentReservation) -> PaymentReservation:
        """Persist updated reservation state."""
