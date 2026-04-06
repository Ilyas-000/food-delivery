"""Delivery assignment domain entity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from src.domain.value_objects.location import Location


class AssignmentStatus(StrEnum):
    """Assignment lifecycle status."""

    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class DeliveryAssignment:
    """Assignment aggregate for courier dispatch."""

    id: UUID
    order_id: UUID
    restaurant_id: UUID
    courier_id: UUID
    status: AssignmentStatus
    current_location: Location | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, order_id: UUID, restaurant_id: UUID, courier_id: UUID) -> "DeliveryAssignment":
        """Create assignment with initial status."""
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            order_id=order_id,
            restaurant_id=restaurant_id,
            courier_id=courier_id,
            status=AssignmentStatus.ASSIGNED,
            current_location=None,
            delivered_at=None,
            created_at=now,
            updated_at=now,
        )

    def cancel(self) -> None:
        """Cancel assignment."""
        if self.status == AssignmentStatus.CANCELLED:
            return
        if self.status == AssignmentStatus.COMPLETED:
            raise ValueError("cannot cancel completed delivery")

        self.status = AssignmentStatus.CANCELLED
        self.updated_at = datetime.now(UTC)

    def update_location(self, location: Location) -> None:
        """Update courier location for assignment."""
        if self.status == AssignmentStatus.CANCELLED:
            raise ValueError("cannot update location for cancelled delivery")
        if self.status == AssignmentStatus.COMPLETED:
            raise ValueError("cannot update location for completed delivery")

        self.current_location = location
        if self.status == AssignmentStatus.ASSIGNED:
            self.status = AssignmentStatus.IN_TRANSIT
        self.updated_at = datetime.now(UTC)

    def complete(self) -> None:
        """Mark assignment as completed."""
        if self.status == AssignmentStatus.COMPLETED:
            return
        if self.status == AssignmentStatus.CANCELLED:
            raise ValueError("cannot complete cancelled delivery")

        now = datetime.now(UTC)
        self.status = AssignmentStatus.COMPLETED
        self.delivered_at = now
        self.updated_at = now
