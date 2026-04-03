"""Exception handlers for Delivery Service."""

from datetime import UTC, datetime
from typing import Any
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.delivery import (
    DeliveryAssignmentNotFoundError,
    DeliveryInvalidStateError,
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


async def assignment_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle missing assignment errors."""
    error = exc
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=str(error),
    )


async def invalid_state_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle invalid delivery lifecycle transitions."""
    error = exc
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="BUSINESS_RULE_VIOLATION",
        message=str(error),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers."""
    app.add_exception_handler(
        DeliveryAssignmentNotFoundError,
        assignment_not_found_handler,
    )
    app.add_exception_handler(
        DeliveryInvalidStateError,
        invalid_state_handler,
    )
