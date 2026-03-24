"""Order-specific domain exceptions."""

from src.domain.exceptions.base import DomainError


class InvalidOrderDataError(DomainError):
    """Raised when order data violates business rules."""


class InvalidOrderTransitionError(DomainError):
    """Raised when order status transition is not allowed."""


class OrderNotFoundError(DomainError):
    """Raised when order does not exist."""


class OrderSagaFailedError(DomainError):
    """Raised when saga orchestration fails."""
