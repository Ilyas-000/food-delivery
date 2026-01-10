"""
Pydantic schemas for authentication endpoints.

Pydantic vs DTOs (important distinction):

Pydantic Schemas:
- HTTP API layer (FastAPI request/response)
- Basic type parsing
- OpenAPI documentation
- JSON serialization

DTOs (application layer):
- Between use cases and other layers
- Pydantic models for internal data
- No HTTP concerns

Flow:
HTTP Request → Pydantic Schema → DTO → Use Case → DTO → Pydantic Schema → HTTP Response
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.application.dto.auth import AuthTokensDTO
from src.application.dto.user import UserResponseDTO
from src.domain.value_objects.user_role import UserRole


class RegisterRequest(BaseModel):
    """
    Request schema for user registration.

    IMPORTANT: This schema only validates HTTP input types.
    All business validation (email format, password strength, name length, etc.)
    is performed at the Domain layer (Clean Architecture principle).
    """

    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CUSTOMER
    phone: str | None = None


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


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: str
    password: str


class RefreshRequest(BaseModel):
    """Request schema for refresh token."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request schema for logout (refresh token revocation)."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Response schema for access + refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str
    access_expires_in: int
    refresh_expires_in: int

    @classmethod
    def from_dto(cls, dto: AuthTokensDTO) -> "TokenResponse":
        """Convert AuthTokensDTO to Pydantic response schema."""
        return cls(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
            access_expires_in=dto.access_expires_in,
            refresh_expires_in=dto.refresh_expires_in,
        )
