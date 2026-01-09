"""
Shared exception types for infrastructure and HTTP boundaries.

Philosophy:
- Keep shared errors generic and technical (infra + HTTP clients).
- Service-specific domain errors must live inside each service.
"""

from typing import Any


class AppError(Exception):
    """Base app error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


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


# Legacy aliases (keep only infra + HTTP)
AppException = AppError
InfrastructureException = InfrastructureError
DatabaseException = DatabaseError
MessageBrokerException = MessageBrokerError
CacheException = CacheError
ExternalServiceException = ExternalServiceError
ServiceUnavailableException = ServiceUnavailableError
HTTPException = HTTPError
BadRequestException = BadRequestError
UnauthorizedException = UnauthorizedError
ForbiddenException = ForbiddenError
NotFoundException = NotFoundError
SharedError = AppError
