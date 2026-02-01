"""Exception handlers - map domain exceptions to HTTP responses."""

from datetime import UTC, datetime
from typing import Any, cast
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

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


def _create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create standardized error response following API_CONVENTIONS.md."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {},
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        },
    )


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Generic handler for all domain errors."""
    error = cast(DomainError, exc)
    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="VALIDATION_ERROR",
        message=error.message,
        details=error.details,
    )


async def restaurant_already_exists_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for RestaurantAlreadyExistsError."""
    error = cast(RestaurantAlreadyExistsError, exc)
    return _create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_code="CONFLICT",
        message=error.message,
        details=error.details,
    )


async def restaurant_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for RestaurantNotFoundError."""
    error = cast(RestaurantNotFoundError, exc)
    return _create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
        message=error.message,
        details=error.details,
    )


async def invalid_restaurant_data_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for InvalidRestaurantDataError."""
    error = cast(InvalidRestaurantDataError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


async def restaurant_not_owned_by_user_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for RestaurantNotOwnedByUserError."""
    error = cast(RestaurantNotOwnedByUserError, exc)
    return _create_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="FORBIDDEN",
        message=error.message,
        details=error.details,
    )


async def menu_item_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for MenuItemNotFoundError."""
    error = cast(MenuItemNotFoundError, exc)
    return _create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
        message=error.message,
        details=error.details,
    )


async def invalid_menu_item_data_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for InvalidMenuItemDataError."""
    error = cast(InvalidMenuItemDataError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


async def menu_item_not_in_restaurant_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for MenuItemNotInRestaurantError."""
    error = cast(MenuItemNotInRestaurantError, exc)
    return _create_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="FORBIDDEN",
        message=error.message,
        details=error.details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers with FastAPI app."""
    # Restaurant handlers
    app.add_exception_handler(RestaurantAlreadyExistsError, restaurant_already_exists_handler)
    app.add_exception_handler(RestaurantNotFoundError, restaurant_not_found_handler)
    app.add_exception_handler(InvalidRestaurantDataError, invalid_restaurant_data_handler)
    app.add_exception_handler(RestaurantNotOwnedByUserError, restaurant_not_owned_by_user_handler)

    # MenuItem handlers
    app.add_exception_handler(MenuItemNotFoundError, menu_item_not_found_handler)
    app.add_exception_handler(InvalidMenuItemDataError, invalid_menu_item_data_handler)
    app.add_exception_handler(MenuItemNotInRestaurantError, menu_item_not_in_restaurant_handler)

    # Generic fallback handler
    app.add_exception_handler(DomainError, domain_error_handler)
