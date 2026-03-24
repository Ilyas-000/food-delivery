"""Base domain exceptions for Order Service."""

from typing import Any


class DomainError(Exception):
    """Base class for domain-level errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return error message."""
        return self.message
