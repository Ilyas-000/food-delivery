"""
MenuItem DTOs (Data Transfer Objects).

DTOs are used to transfer data between application layers.
They are Pydantic models for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities import MenuItem
from src.domain.value_objects import Availability, Category


class CreateMenuItemDTO(BaseModel):
    """DTO for creating a new menu item."""

    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=1000)
    price_amount: Decimal = Field(ge=0)
    category: Category
    image_url: str | None = Field(default=None, max_length=500)


class UpdateMenuItemDTO(BaseModel):
    """DTO for updating menu item information."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price_amount: Decimal | None = Field(default=None, ge=0)
    category: Category | None = None
    image_url: str | None = Field(default=None, max_length=500)


class MenuItemResponseDTO(BaseModel):
    """DTO for menu item response."""

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
    def from_entity(cls, menu_item: MenuItem) -> "MenuItemResponseDTO":
        """
        Convert MenuItem entity to DTO.

        Args:
            menu_item: MenuItem entity

        Returns:
            MenuItemResponseDTO: DTO for API response
        """
        return cls(
            id=menu_item.id,
            restaurant_id=menu_item.restaurant_id,
            name=menu_item.name,
            description=menu_item.description,
            price_amount=menu_item.price.amount,
            price_currency=menu_item.price.currency,
            category=menu_item.category,
            image_url=menu_item.image_url,
            availability=menu_item.availability,
            created_at=menu_item.created_at,
            updated_at=menu_item.updated_at,
        )
