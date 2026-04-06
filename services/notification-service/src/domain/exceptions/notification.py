"""Notification domain exceptions."""


class NotificationError(Exception):
    """Base exception for notification domain errors."""


class NotificationNotFoundError(NotificationError):
    """Raised when notification does not exist."""


class NotificationValidationError(NotificationError):
    """Raised when notification data is invalid."""


class NotificationTemplateNotFoundError(NotificationError):
    """Raised when template is not registered."""
