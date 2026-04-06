"""Base review domain exceptions."""

from typing import Any


class DomainError(Exception):
    """Base domain exception with structured metadata."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ReviewNotFoundError(DomainError):
    """Raised when review does not exist."""


class ReviewAlreadyExistsError(DomainError):
    """Raised when review already exists for order and author."""


class InvalidReviewDataError(DomainError):
    """Raised when review data breaks business rules."""


class ReviewForbiddenError(DomainError):
    """Raised when user cannot mutate requested review."""


class ReviewUnauthorizedError(DomainError):
    """Raised when current user identity is missing or invalid."""
