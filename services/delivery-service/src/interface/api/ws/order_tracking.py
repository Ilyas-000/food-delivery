"""WebSocket endpoints for order tracking."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from src.interface.dependencies.delivery import get_order_tracking_broadcaster
from src.interface.realtime.order_tracking_broadcaster import OrderTrackingBroadcaster

router = APIRouter(tags=["order-tracking"])


@router.websocket("/ws/orders/{order_id}")
async def track_order(
    websocket: WebSocket,
    order_id: UUID,
    broadcaster: Annotated[OrderTrackingBroadcaster, Depends(get_order_tracking_broadcaster)],
) -> None:
    """Subscribe client to order tracking events."""
    await broadcaster.connect(order_id=order_id, websocket=websocket)
    try:
        while True:
            # The server is push-only, but we keep the connection alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(order_id=order_id, websocket=websocket)
