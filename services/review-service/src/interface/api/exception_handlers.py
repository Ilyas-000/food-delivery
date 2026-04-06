"""Exception handlers for review-service."""

from datetime import UTC, datetime
from typing import Any, cast
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import (
    DomainError,
    InvalidReviewDataError,
    ReviewAlreadyExistsError,
    ReviewForbiddenError,
    ReviewNotFoundError,
    ReviewUnauthorizedError,
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


async def review_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle missing review errors."""
    error = cast(ReviewNotFoundError, exc)
    return _error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", error.message, error.details)


async def review_already_exists_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle duplicate review errors."""
    error = cast(ReviewAlreadyExistsError, exc)
    return _error_response(status.HTTP_409_CONFLICT, "CONFLICT", error.message, error.details)


async def invalid_review_data_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle review validation errors."""
    error = cast(InvalidReviewDataError, exc)
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "BUSINESS_RULE_VIOLATION",
        error.message,
        error.details,
    )


async def review_forbidden_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle forbidden review actions."""
    error = cast(ReviewForbiddenError, exc)
    return _error_response(
        status.HTTP_403_FORBIDDEN,
        "FORBIDDEN",
        error.message,
        error.details,
    )


async def review_unauthorized_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle missing gateway identity."""
    error = cast(ReviewUnauthorizedError, exc)
    return _error_response(
        status.HTTP_401_UNAUTHORIZED,
        "UNAUTHORIZED",
        error.message,
        error.details,
    )


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Generic domain error fallback."""
    error = cast(DomainError, exc)
    return _error_response(
        status.HTTP_400_BAD_REQUEST,
        "VALIDATION_ERROR",
        error.message,
        error.details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register review-service exception handlers."""
    app.add_exception_handler(ReviewNotFoundError, review_not_found_handler)
    app.add_exception_handler(ReviewAlreadyExistsError, review_already_exists_handler)
    app.add_exception_handler(InvalidReviewDataError, invalid_review_data_handler)
    app.add_exception_handler(ReviewForbiddenError, review_forbidden_handler)
    app.add_exception_handler(ReviewUnauthorizedError, review_unauthorized_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
