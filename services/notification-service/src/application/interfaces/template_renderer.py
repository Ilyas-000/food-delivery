"""Notification template rendering contract."""

from abc import ABC, abstractmethod
from typing import Any

from src.application.dto.notification import RenderedNotificationDTO


class ITemplateRenderer(ABC):
    """Template rendering contract."""

    @abstractmethod
    def render(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> RenderedNotificationDTO:
        """Render notification content from template context."""
