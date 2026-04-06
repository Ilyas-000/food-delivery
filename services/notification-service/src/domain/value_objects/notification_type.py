"""Notification type value object."""

from enum import StrEnum


class NotificationType(StrEnum):
    """Supported notification delivery channels."""

    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
