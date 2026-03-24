"""API schemas for delivery endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.application.dto.delivery import DeliveryAssignmentResponseDTO


class AssignCourierRequest(BaseModel):
    """Request schema for courier assignment."""

    order_id: UUID
    restaurant_id: UUID


class DeliveryAssignmentResponse(BaseModel):
    """Response schema for delivery assignment."""

    assignment_id: UUID
    order_id: UUID
    restaurant_id: UUID
    status: str
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
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
