"""
User-related DTOs.

DTOs are used for data transfer between layers, without business logic.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole


class RegisterUserDTO(BaseModel):
    """DTO for user registration input."""

    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CUSTOMER
    phone: str | None = None


class UserResponseDTO(BaseModel):
    """
    DTO for user data output.
    This excludes sensitive fields like password hash.
    """

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    phone: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, user: User) -> "UserResponseDTO":
        """Create DTO from User entity."""
        return cls(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
