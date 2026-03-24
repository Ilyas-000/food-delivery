"""Delivery DTO models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.assignment import DeliveryAssignment


class AssignCourierDTO(BaseModel):
    """Input payload for courier assignment."""

    order_id: UUID
    restaurant_id: UUID


class DeliveryAssignmentResponseDTO(BaseModel):
    """Output payload for assignment state."""

    id: UUID
    order_id: UUID
    restaurant_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, assignment: DeliveryAssignment) -> "DeliveryAssignmentResponseDTO":
        """Build response DTO from domain entity."""
        return cls(
            id=assignment.id,
            order_id=assignment.order_id,
            restaurant_id=assignment.restaurant_id,
            status=assignment.status.value,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )
