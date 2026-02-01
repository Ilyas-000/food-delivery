"""Domain exceptions."""

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.menu_item import (
    InvalidMenuItemDataError,
    MenuItemNotFoundError,
    MenuItemNotInRestaurantError,
)
from src.domain.exceptions.restaurant import (
    InvalidRestaurantDataError,
    RestaurantAlreadyExistsError,
    RestaurantNotFoundError,
    RestaurantNotOwnedByUserError,
)
