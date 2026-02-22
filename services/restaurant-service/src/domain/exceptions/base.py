"""
Base domain exceptions.

All domain exceptions inherit from DomainError.
"""

from typing import Any


class DomainError(Exception):
    """
    Base class for all domain exceptions.

    Domain exceptions represent business rule violations or domain-specific errors.
    They are caught and translated to HTTP responses in the interface layer.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize domain error.

        Args:
            message: Human-readable error message
            details: Optional dict with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation."""
        return self.message

    def __repr__(self) -> str:
        """Developer representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"
