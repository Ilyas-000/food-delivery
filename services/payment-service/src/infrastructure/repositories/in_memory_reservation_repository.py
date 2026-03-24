"""In-memory repository for payment reservations."""

from uuid import UUID

from src.application.interfaces.reservation_repository import IReservationRepository
from src.domain.entities.reservation import PaymentReservation


class InMemoryReservationRepository(IReservationRepository):
    """Simple in-memory persistence for local development and tests."""

    def __init__(self) -> None:
        self._storage: dict[UUID, PaymentReservation] = {}

    async def create(self, reservation: PaymentReservation) -> PaymentReservation:
        """Store reservation."""
        self._storage[reservation.id] = reservation
        return reservation

    async def get_by_id(self, reservation_id: UUID) -> PaymentReservation | None:
        """Load reservation by id."""
        return self._storage.get(reservation_id)

    async def update(self, reservation: PaymentReservation) -> PaymentReservation:
        """Update reservation state."""
        self._storage[reservation.id] = reservation
        return reservation
