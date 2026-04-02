"""Exception handlers for Payment Service."""

from datetime import UTC, datetime
from typing import Any
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.payment import (
    PaymentIdempotencyConflictError,
    PaymentNotFoundError,
    PaymentStateTransitionError,
    PaymentValidationError,
)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        },
    )


async def payment_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle missing payment errors."""
    error = exc
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=str(error),
    )


async def payment_validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle payment validation errors."""
    error = exc
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="BUSINESS_RULE_VIOLATION",
        message=str(error),
    )


async def payment_transition_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle invalid payment state transitions."""
    error = exc
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="CONFLICT",
        message=str(error),
    )


async def payment_idempotency_conflict_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle idempotency conflicts."""
    error = exc
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="CONFLICT",
        message=str(error),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers."""
    app.add_exception_handler(
        PaymentNotFoundError,
        payment_not_found_handler,
    )
    app.add_exception_handler(
        PaymentValidationError,
        payment_validation_error_handler,
    )
    app.add_exception_handler(
        PaymentStateTransitionError,
        payment_transition_error_handler,
    )
    app.add_exception_handler(
        PaymentIdempotencyConflictError,
        payment_idempotency_conflict_handler,
    )
