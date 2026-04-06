"""Delivery DTO models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.assignment import DeliveryAssignment


class AssignCourierDTO(BaseModel):
    """Input payload for courier assignment."""

    order_id: UUID
    restaurant_id: UUID
    courier_id: UUID | None = None


class UpdateDeliveryLocationDTO(BaseModel):
    """Input payload for location update."""

    order_id: UUID
    latitude: float
    longitude: float


class DeliveryAssignmentResponseDTO(BaseModel):
    """Output payload for assignment state."""

    id: UUID
    order_id: UUID
    restaurant_id: UUID
    courier_id: UUID
    status: str
    latitude: float | None
    longitude: float | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, assignment: DeliveryAssignment) -> "DeliveryAssignmentResponseDTO":
        """Build response DTO from domain entity."""
        latitude = None
        longitude = None
        if assignment.current_location is not None:
            latitude = assignment.current_location.latitude
            longitude = assignment.current_location.longitude

        return cls(
            id=assignment.id,
            order_id=assignment.order_id,
            restaurant_id=assignment.restaurant_id,
            courier_id=assignment.courier_id,
            status=assignment.status.value,
            latitude=latitude,
            longitude=longitude,
            delivered_at=assignment.delivered_at,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )
