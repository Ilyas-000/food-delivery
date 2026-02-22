"""Pydantic schemas for menu item endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.application.dto.menu_item_dto import MenuItemResponseDTO
from src.domain.value_objects.availability import Availability
from src.domain.value_objects.category import Category


class MenuItemResponse(BaseModel):
    """Response schema for menu item data."""

    id: UUID
    restaurant_id: UUID
    name: str
    description: str
    price_amount: Decimal
    price_currency: str
    category: Category
    image_url: str | None
    availability: Availability
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: MenuItemResponseDTO) -> "MenuItemResponse":
        """Convert MenuItemResponseDTO to Pydantic response schema."""
        return cls(
            id=dto.id,
            restaurant_id=dto.restaurant_id,
            name=dto.name,
            description=dto.description,
            price_amount=dto.price_amount,
            price_currency=dto.price_currency,
            category=dto.category,
            image_url=dto.image_url,
            availability=dto.availability,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class CreateMenuItemRequest(BaseModel):
    """Request schema for creating a menu item."""

    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=1000)
    price_amount: Decimal = Field(ge=0)
    category: Category
    image_url: str | None = Field(default=None, max_length=500)


class CreateRestaurantMenuItemRequest(BaseModel):
    """Request schema for creating a menu item in a specific restaurant."""

    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=1000)
    price_amount: Decimal = Field(ge=0)
    category: Category
    image_url: str | None = Field(default=None, max_length=500)


class UpdateMenuItemRequest(BaseModel):
    """Request schema for updating menu item."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price_amount: Decimal | None = Field(default=None, ge=0)
    category: Category | None = None
    image_url: str | None = Field(default=None, max_length=500)


class UpdateMenuItemAvailabilityRequest(BaseModel):
    """Request schema for updating menu item availability."""

    availability: Availability
