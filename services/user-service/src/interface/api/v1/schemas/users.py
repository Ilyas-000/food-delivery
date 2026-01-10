"""
Pydantic schemas for user profile endpoints.
"""

from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    """Request schema for updating profile fields."""

    full_name: str | None = None
    phone: str | None = None
