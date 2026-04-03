"""
Event definitions - contracts between microservices.

Events are shared because:
- They define the interface between services
- All services must use the same event structure
- Changes to events affect multiple services

Import explicitly:
    from shared.events.order_events import OrderCreatedEvent, OrderConfirmedEvent
    from shared.events.payment_events import PaymentReservedEvent
    from shared.events.delivery_events import DeliveryAssignedEvent
    from shared.events.base import BaseEvent
"""
