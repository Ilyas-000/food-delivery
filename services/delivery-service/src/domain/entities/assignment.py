"""Delivery assignment domain entity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class AssignmentStatus(StrEnum):
    """Assignment lifecycle status."""

    ASSIGNED = "assigned"
    CANCELLED = "cancelled"


@dataclass
class DeliveryAssignment:
    """Assignment aggregate for courier dispatch."""

    id: UUID
    order_id: UUID
    restaurant_id: UUID
    status: AssignmentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, order_id: UUID, restaurant_id: UUID) -> "DeliveryAssignment":
        """Create assignment with initial status."""
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            order_id=order_id,
            restaurant_id=restaurant_id,
            status=AssignmentStatus.ASSIGNED,
            created_at=now,
            updated_at=now,
        )

    def cancel(self) -> None:
        """Cancel assignment."""
        self.status = AssignmentStatus.CANCELLED
        self.updated_at = datetime.now(UTC)
