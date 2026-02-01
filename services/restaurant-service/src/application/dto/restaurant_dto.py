"""
Restaurant DTOs (Data Transfer Objects).

DTOs are used to transfer data between application layers.
They are Pydantic models for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities import Restaurant
from src.domain.value_objects import Cuisine


class CreateRestaurantDTO(BaseModel):
    """DTO for creating a new restaurant."""

    owner_id: UUID
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)
    street: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=5, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    cuisine: Cuisine


class UpdateRestaurantDTO(BaseModel):
    """DTO for updating restaurant information."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    street: str | None = Field(default=None, min_length=2, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=5, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    cuisine: Cuisine | None = None


class RestaurantResponseDTO(BaseModel):
    """DTO for restaurant response."""

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
    def from_entity(cls, restaurant: Restaurant) -> "RestaurantResponseDTO":
        """
        Convert Restaurant entity to DTO.

        Args:
            restaurant: Restaurant entity

        Returns:
            RestaurantResponseDTO: DTO for API response
        """
        return cls(
            id=restaurant.id,
            owner_id=restaurant.owner_id,
            name=restaurant.name,
            description=restaurant.description,
            street=restaurant.address.street,
            city=restaurant.address.city,
            postal_code=restaurant.address.postal_code,
            latitude=restaurant.address.latitude,
            longitude=restaurant.address.longitude,
            cuisine=restaurant.cuisine,
            rating=restaurant.rating,
            is_active=restaurant.is_active,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at,
        )


class SearchRestaurantsDTO(BaseModel):
    """DTO for restaurant search filters."""

    cuisine: Cuisine | None = None
    city: str | None = None
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    is_active: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
