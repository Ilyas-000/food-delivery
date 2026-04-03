"""API schemas for delivery endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.delivery import DeliveryAssignmentResponseDTO


class AssignCourierRequest(BaseModel):
    """Request schema for courier assignment."""

    order_id: UUID
    restaurant_id: UUID


class UpdateDeliveryLocationRequest(BaseModel):
    """Request schema for courier location update."""

    order_id: UUID
    latitude: Annotated[float, Field(ge=-90.0, le=90.0)]
    longitude: Annotated[float, Field(ge=-180.0, le=180.0)]


class DeliveryAssignmentResponse(BaseModel):
    """Response schema for delivery assignment."""

    assignment_id: UUID
    order_id: UUID
    restaurant_id: UUID
    status: str
    latitude: float | None
    longitude: float | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: DeliveryAssignmentResponseDTO) -> "DeliveryAssignmentResponse":
        """Build API response from DTO."""
        return cls(
            assignment_id=dto.id,
            order_id=dto.order_id,
            restaurant_id=dto.restaurant_id,
            status=dto.status,
            latitude=dto.latitude,
            longitude=dto.longitude,
            delivered_at=dto.delivered_at,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
