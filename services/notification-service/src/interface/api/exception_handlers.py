"""Exception handlers for Notification Service."""

from datetime import UTC, datetime
from typing import Any
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.notification import (
    NotificationNotFoundError,
    NotificationTemplateNotFoundError,
    NotificationValidationError,
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


async def notification_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle missing notification errors."""
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=str(exc),
    )


async def notification_validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle invalid notification data."""
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="BUSINESS_RULE_VIOLATION",
        message=str(exc),
    )


async def template_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unknown template names."""
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=str(exc),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers."""
    app.add_exception_handler(NotificationNotFoundError, notification_not_found_handler)
    app.add_exception_handler(NotificationValidationError, notification_validation_error_handler)
    app.add_exception_handler(NotificationTemplateNotFoundError, template_not_found_handler)
