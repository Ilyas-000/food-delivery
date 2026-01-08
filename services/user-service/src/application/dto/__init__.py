"""
DTOs (Data Transfer Objects) - objects for transferring data between layers.

DTOs vs Domain Entities (important for interviews):

DTOs:
- For data transfer (API input/output, between services)
- Simple, no business logic
- Can be use-case specific
- Easy to serialize

Domain Entities:
- For business logic
- Contain rules and methods
- Independent of external representations

Why not use entities directly in API?
1. Security - we can hide fields (password_hash)
2. Versioning - API v1/v2 with different DTOs, one Entity
3. Decoupling - domain changes don't break API contract

Import explicitly:
    from application.dto import RegisterUserDTO, UserResponseDTO
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole


class RegisterUserDTO(BaseModel):
    """
    DTO for user registration input.

    Used by RegisterUserUseCase as input parameter.
    Usually created from API request (Pydantic schema).

    Attributes:
        email: User email (raw string, will be converted to Email VO)
        password: Plain text password (will be hashed)
        full_name: Full name
        role: User role (default CUSTOMER)
        phone: Optional phone number
    """

    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CUSTOMER
    phone: str | None = None


class UserResponseDTO(BaseModel):
    """
    DTO for user data output.

    Used by Use Cases to return user data to API layer.
    Contains only data that should be exposed to clients.

    IMPORTANT: NO password_hash or other sensitive data!

    Attributes:
        id: User UUID
        email: User email
        full_name: Full name
        role: User role
        is_active: Active status
        phone: Phone number
        created_at: Creation timestamp
        updated_at: Last update timestamp
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
        """
        Create DTO from User entity.

        Factory method for Entity → DTO conversion.
        This is important pattern: conversion happens in DTO, not in Entity.

        Args:
            user: User entity

        Returns:
            UserResponseDTO: DTO for API response

        Example:
            user = await repository.get_by_id(user_id)
            dto = UserResponseDTO.from_entity(user)
            return dto  # to API layer
        """
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
