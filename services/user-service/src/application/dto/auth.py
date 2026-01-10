"""
Auth-related DTOs.

Keep auth DTOs separate from user profile DTOs for clarity.
"""

from pydantic import BaseModel

from src.domain.value_objects.user_role import UserRole


class RegisterUserDTO(BaseModel):
    """DTO for user registration input."""

    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.CUSTOMER
    phone: str | None = None


class LoginUserDTO(BaseModel):
    """DTO for user login input."""

    email: str
    password: str


class RefreshTokenDTO(BaseModel):
    """DTO for refresh token input."""

    refresh_token: str


class LogoutUserDTO(BaseModel):
    """DTO for logout input (refresh token revocation)."""

    refresh_token: str


class AuthTokensDTO(BaseModel):
    """DTO for auth token pair output."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    refresh_expires_in: int
