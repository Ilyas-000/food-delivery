"""Contracts for notification delivery channels."""

from abc import ABC, abstractmethod


class IEmailClient(ABC):
    """Email delivery contract."""

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str) -> str:
        """Send email and return provider message id."""


class IPushClient(ABC):
    """Push delivery contract."""

    @abstractmethod
    async def send(self, recipient: str, title: str, body: str) -> str:
        """Send push notification and return provider message id."""
