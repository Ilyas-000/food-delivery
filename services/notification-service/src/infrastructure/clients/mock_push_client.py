"""Mock push client."""

from collections.abc import Sequence
from dataclasses import dataclass

from src.application.interfaces.channel_clients import IPushClient


@dataclass(frozen=True)
class MockPushMessage:
    """Recorded mock push message."""

    recipient: str
    title: str
    body: str
    provider_message_id: str


class MockPushClient(IPushClient):
    """In-memory mock push sender."""

    def __init__(self) -> None:
        self._messages: list[MockPushMessage] = []

    async def send(self, recipient: str, title: str, body: str) -> str:
        """Store push payload and return deterministic message id."""
        provider_message_id = f"push-{len(self._messages) + 1}"
        self._messages.append(
            MockPushMessage(
                recipient=recipient,
                title=title,
                body=body,
                provider_message_id=provider_message_id,
            )
        )
        return provider_message_id

    @property
    def messages(self) -> Sequence[MockPushMessage]:
        """Return captured push messages."""
        return tuple(self._messages)

    def clear(self) -> None:
        """Reset captured message history."""
        self._messages.clear()
