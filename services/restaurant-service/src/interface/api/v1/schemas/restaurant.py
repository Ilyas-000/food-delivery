"""Pydantic schemas for restaurant endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.restaurant_dto import RestaurantResponseDTO
from src.domain.value_objects.cuisine import Cuisine


class RestaurantResponse(BaseModel):
    """Response schema for restaurant data."""

    id: UUID
    owner_id: UUID
    name: str
    description: str
    street: str
    city: str
    postal_code: str
    latitude: float | None
    longitude: float | None
    cuisine: Cuisine
    rating: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: RestaurantResponseDTO) -> "RestaurantResponse":
        """Convert RestaurantResponseDTO to Pydantic response schema."""
        return cls(
            id=dto.id,
            owner_id=dto.owner_id,
            name=dto.name,
            description=dto.description,
            street=dto.street,
            city=dto.city,
            postal_code=dto.postal_code,
            latitude=dto.latitude,
            longitude=dto.longitude,
            cuisine=dto.cuisine,
            rating=dto.rating,
            is_active=dto.is_active,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class CreateRestaurantRequest(BaseModel):
    """Request schema for creating a restaurant."""

    owner_id: UUID
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)
    street: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=5, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    cuisine: Cuisine


class UpdateRestaurantRequest(BaseModel):
    """Request schema for updating restaurant."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    street: str | None = Field(default=None, min_length=2, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=5, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    cuisine: Cuisine | None = None


class SearchRestaurantsRequest(BaseModel):
    """Request schema for searching restaurants."""

    cuisine: Cuisine | None = None
    city: str | None = None
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    is_active: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
