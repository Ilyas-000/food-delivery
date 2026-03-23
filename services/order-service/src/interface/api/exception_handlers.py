"""Exception handlers mapping domain errors to API responses."""

from datetime import UTC, datetime
from typing import Any, cast
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.order import (
    InvalidOrderDataError,
    InvalidOrderTransitionError,
    OrderNotFoundError,
    OrderSagaFailedError,
)


def _create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build standardized error response."""
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
    """Fallback handler for domain errors."""
    error = cast(DomainError, exc)
    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="VALIDATION_ERROR",
        message=error.message,
        details=error.details,
    )


async def order_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for missing order."""
    error = cast(OrderNotFoundError, exc)
    return _create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
        message=error.message,
        details=error.details,
    )


async def invalid_order_data_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for domain validation errors."""
    error = cast(InvalidOrderDataError | InvalidOrderTransitionError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


async def order_saga_failed_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handler for saga failures."""
    error = cast(OrderSagaFailedError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""
    app.add_exception_handler(OrderNotFoundError, order_not_found_handler)
    app.add_exception_handler(InvalidOrderDataError, invalid_order_data_handler)
    app.add_exception_handler(InvalidOrderTransitionError, invalid_order_data_handler)
    app.add_exception_handler(OrderSagaFailedError, order_saga_failed_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
