"""
Pydantic schemas for user profile endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.application.dto.user import UserResponseDTO
from src.domain.value_objects.user_role import UserRole


class UserResponse(BaseModel):
    """
    Response schema for user data.

    IMPORTANT: Does NOT include password_hash or other sensitive data!

    This is public-facing representation of User entity.
    Used in registration response, profile endpoints, etc.

    """

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    phone: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: UserResponseDTO) -> "UserResponse":
        """
        Convert UserResponseDTO to Pydantic response schema.

        This is the mapping between application layer (DTO) and API layer (Pydantic).

        Args:
            dto: UserResponseDTO from use case

        Returns:
            UserResponse: Pydantic schema for HTTP response

        Example:
            dto = await use_case.execute(...)
            response = UserResponse.from_dto(dto)
            return response  # FastAPI serializes to JSON
        """
        return cls(
            id=dto.id,
            email=dto.email,
            full_name=dto.full_name,
            role=dto.role,
            is_active=dto.is_active,
            phone=dto.phone,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class UpdateProfileRequest(BaseModel):
    """Request schema for updating profile fields."""

    full_name: str | None = None
    phone: str | None = None
