"""Exception handlers for Analytics Service."""

from datetime import UTC, datetime
from typing import Any
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.analytics import AnalyticsValidationError


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


async def analytics_validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle invalid analytics queries."""
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="BUSINESS_RULE_VIOLATION",
        message=str(exc),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers."""
    app.add_exception_handler(AnalyticsValidationError, analytics_validation_error_handler)
