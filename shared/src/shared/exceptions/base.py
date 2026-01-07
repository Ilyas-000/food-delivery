"""Shared exception types."""

from typing import Any

# Base errors


class AppError(Exception):
    """Base app error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Domain errors


class DomainError(AppError):
    """Base domain error."""


class EntityNotFoundError(DomainError):
    """Domain entity not found."""


class BusinessRuleViolationError(DomainError):
    """Business rule violated."""


class InvalidOperationError(DomainError):
    """Invalid operation for state."""


class ValidationError(DomainError):
    """Domain validation failed."""


class ConflictError(DomainError):
    """Resource conflict."""


# Infrastructure errors


class InfrastructureError(AppError):
    """Base infrastructure error."""


class DatabaseError(InfrastructureError):
    """Database error."""


class MessageBrokerError(InfrastructureError):
    """Broker error."""


class CacheError(InfrastructureError):
    """Cache error."""


class ExternalServiceError(InfrastructureError):
    """External service error."""


class ServiceUnavailableError(InfrastructureError):
    """Dependency unavailable."""


# Auth errors


class AuthenticationError(AppError):
    """Auth error base."""


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials."""


class TokenExpiredError(AuthenticationError):
    """JWT expired."""


class InvalidTokenError(AuthenticationError):
    """JWT invalid."""


class AuthorizationError(AppError):
    """Forbidden."""


# HTTP errors


class HTTPError(AppError):
    """HTTP error base."""

    def __init__(
        self,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code


class BadRequestError(HTTPError):
    """HTTP 400."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=400, details=details)


class UnauthorizedError(HTTPError):
    """HTTP 401."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=401, details=details)


class ForbiddenError(HTTPError):
    """HTTP 403."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=403, details=details)


class NotFoundError(HTTPError):
    """HTTP 404."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=404, details=details)


# Legacy aliases
AppException = AppError
DomainException = DomainError
EntityNotFoundException = EntityNotFoundError
BusinessRuleViolationException = BusinessRuleViolationError
InvalidOperationException = InvalidOperationError
InfrastructureException = InfrastructureError
DatabaseException = DatabaseError
MessageBrokerException = MessageBrokerError
CacheException = CacheError
ExternalServiceException = ExternalServiceError
ServiceUnavailableException = ServiceUnavailableError
AuthenticationException = AuthenticationError
InvalidCredentialsException = InvalidCredentialsError
TokenExpiredException = TokenExpiredError
InvalidTokenException = InvalidTokenError
AuthorizationException = AuthorizationError
HTTPException = HTTPError
BadRequestException = BadRequestError
UnauthorizedException = UnauthorizedError
ForbiddenException = ForbiddenError
NotFoundException = NotFoundError
SharedError = AppError
