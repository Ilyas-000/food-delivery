"""In-memory notification templates."""

from typing import Any

from src.application.dto.notification import RenderedNotificationDTO
from src.application.interfaces.template_renderer import ITemplateRenderer
from src.domain.exceptions.notification import (
    NotificationTemplateNotFoundError,
    NotificationValidationError,
)

_TEMPLATES: dict[str, tuple[str, str]] = {
    "order_created_email": (
        "Order {order_id} received",
        "We received your order {order_id} and started processing it.",
    ),
    "order_confirmed_email": (
        "Order {order_id} confirmed",
        "Your order {order_id} has been confirmed and is being prepared.",
    ),
    "order_confirmed_push": (
        "Order confirmed",
        "Order {order_id} is confirmed and being prepared.",
    ),
    "courier_assigned_email": (
        "Courier assigned for order {order_id}",
        "A courier was assigned to order {order_id}.",
    ),
    "courier_assigned_push": (
        "Courier assigned",
        "Courier is assigned to order {order_id}.",
    ),
}


class InMemoryTemplateRenderer(ITemplateRenderer):
    """Render notification content from in-memory templates."""

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> RenderedNotificationDTO:
        """Render template subject and body."""
        if template_name not in _TEMPLATES:
            raise NotificationTemplateNotFoundError(f"template '{template_name}' not found")

        subject_template, body_template = _TEMPLATES[template_name]
        try:
            subject = subject_template.format(**context)
            body = body_template.format(**context)
        except KeyError as error:
            missing_key = error.args[0]
            raise NotificationValidationError(
                f"template '{template_name}' requires '{missing_key}'"
            ) from error

        return RenderedNotificationDTO(subject=subject, body=body)
