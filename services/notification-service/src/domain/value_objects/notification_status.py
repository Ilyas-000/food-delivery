"""Notification status value object."""

from enum import StrEnum


class NotificationStatus(StrEnum):
    """Notification lifecycle status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
