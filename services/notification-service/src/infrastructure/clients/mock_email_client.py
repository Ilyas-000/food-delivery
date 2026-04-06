"""Mock email client."""

from collections.abc import Sequence
from dataclasses import dataclass

from src.application.interfaces.channel_clients import IEmailClient


@dataclass(frozen=True)
class MockEmailMessage:
    """Recorded mock email message."""

    recipient: str
    subject: str
    body: str
    provider_message_id: str


class MockEmailClient(IEmailClient):
    """In-memory mock email sender."""

    def __init__(self) -> None:
        self._messages: list[MockEmailMessage] = []

    async def send(self, recipient: str, subject: str, body: str) -> str:
        """Store email payload and return deterministic message id."""
        provider_message_id = f"email-{len(self._messages) + 1}"
        self._messages.append(
            MockEmailMessage(
                recipient=recipient,
                subject=subject,
                body=body,
                provider_message_id=provider_message_id,
            )
        )
        return provider_message_id

    @property
    def messages(self) -> Sequence[MockEmailMessage]:
        """Return captured email messages."""
        return tuple(self._messages)

    def clear(self) -> None:
        """Reset captured message history."""
        self._messages.clear()
