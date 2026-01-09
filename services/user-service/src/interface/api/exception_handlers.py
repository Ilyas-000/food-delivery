"""
Exception handlers - map domain exceptions to HTTP responses.

Architecture principle:
Domain exceptions should NOT leak to HTTP layer.
Exception handlers provide clean boundary between layers.

Mapping:
- UserAlreadyExistsError → 409 Conflict (CONFLICT)
- InvalidEmailError → 422 Unprocessable Entity (BUSINESS_RULE_VIOLATION)
- InvalidCredentialsError → 401 Unauthorized (UNAUTHORIZED)
- InvalidTokenError → 401 Unauthorized (UNAUTHORIZED)
- UserNotFoundError → 404 Not Found (NOT_FOUND)
- DomainError (generic) → 400 Bad Request (VALIDATION_ERROR)

Error format follows docs/API_CONVENTIONS.md:
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...},
    "request_id": "uuid",
    "timestamp": "ISO 8601"
  }
}

Interview note:
This is separation of concerns - domain doesn't know about HTTP,
API layer translates domain concepts to HTTP concepts.
"""

from datetime import UTC, datetime
from typing import Any, cast
import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import (
    DomainError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


def _create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Create standardized error response following API_CONVENTIONS.md.

    Args:
        status_code: HTTP status code
        error_code: Error code from API conventions
        message: Human-readable error message
        details: Additional error details (optional)

    Returns:
        JSONResponse: Standardized error response
    """
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
    """
    Generic handler for all domain errors.

    This is fallback handler for DomainError base class.
    Specific exceptions (UserAlreadyExistsError) have their own handlers.

    Args:
        request: FastAPI request
        exc: Domain exception

    Returns:
        JSONResponse: 400 Bad Request with error details
    """
    error = cast(DomainError, exc)
    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="VALIDATION_ERROR",
        message=error.message,
        details=error.details,
    )


async def user_already_exists_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for UserAlreadyExistsError.

    HTTP semantics:
    409 Conflict - resource already exists (duplicate)

    Args:
        request: FastAPI request
        exc: UserAlreadyExistsError

    Returns:
        JSONResponse: 409 Conflict
    """
    error = cast(UserAlreadyExistsError, exc)
    return _create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_code="CONFLICT",
        message=error.message,
        details=error.details,
    )


async def user_not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for UserNotFoundError.

    HTTP semantics:
    404 Not Found - requested resource doesn't exist

    Args:
        request: FastAPI request
        exc: UserNotFoundError

    Returns:
        JSONResponse: 404 Not Found
    """
    error = cast(UserNotFoundError, exc)
    return _create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
        message=error.message,
        details=error.details,
    )


async def invalid_email_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for InvalidEmailError.

    HTTP semantics:
    422 Unprocessable Entity - validation error (business rule violation)

    Args:
        request: FastAPI request
        exc: InvalidEmailError

    Returns:
        JSONResponse: 422 Unprocessable Entity
    """
    error = cast(InvalidEmailError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


async def invalid_password_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for InvalidPasswordError.

    HTTP semantics:
    422 Unprocessable Entity - validation error (business rule violation)

    Args:
        request: FastAPI request
        exc: InvalidPasswordError

    Returns:
        JSONResponse: 422 Unprocessable Entity
    """
    error = cast(InvalidPasswordError, exc)
    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="BUSINESS_RULE_VIOLATION",
        message=error.message,
        details=error.details,
    )


async def invalid_credentials_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for InvalidCredentialsError.

    HTTP semantics:
    401 Unauthorized - invalid credentials
    """
    error = cast(InvalidCredentialsError, exc)
    return _create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="UNAUTHORIZED",
        message=error.message,
        details=error.details,
    )


async def invalid_token_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for InvalidTokenError.

    HTTP semantics:
    401 Unauthorized - invalid or expired token
    """
    error = cast(InvalidTokenError, exc)
    return _create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="UNAUTHORIZED",
        message=error.message,
        details=error.details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all domain exception handlers with FastAPI app.

    Call this during app initialization in main.py.

    Args:
        app: FastAPI application instance

    Example:
        app = FastAPI()
        register_exception_handlers(app)
    """
    # Specific handlers (higher priority)
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(InvalidEmailError, invalid_email_handler)
    app.add_exception_handler(InvalidPasswordError, invalid_password_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(InvalidTokenError, invalid_token_handler)

    # Generic fallback handler
    app.add_exception_handler(DomainError, domain_error_handler)
