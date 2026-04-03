"""Delivery domain exceptions."""


class DeliveryError(Exception):
    """Base exception for delivery domain errors."""


class DeliveryAssignmentNotFoundError(DeliveryError):
    """Raised when assignment does not exist."""


class DeliveryInvalidStateError(DeliveryError):
    """Raised when delivery state transition is invalid."""
