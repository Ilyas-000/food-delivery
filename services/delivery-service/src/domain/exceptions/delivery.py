"""Delivery domain exceptions."""


class DeliveryError(Exception):
    """Base exception for delivery domain errors."""


class DeliveryAssignmentNotFoundError(DeliveryError):
    """Raised when assignment does not exist."""
