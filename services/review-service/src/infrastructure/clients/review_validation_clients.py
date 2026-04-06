"""HTTP clients for order and delivery validation."""

from uuid import UUID

import httpx

from src.application.dto.review import DeliverySnapshotDTO, OrderSnapshotDTO
from src.application.interfaces.validation_clients import (
    IDeliveryValidationClient,
    IOrderValidationClient,
)

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500


class _BaseHttpClient:
    """Shared HTTP helper."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def _request(self, method: str, path: str) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                return await client.request(method=method, url=path)
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"request timeout calling '{self._base_url}{path}'") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"request error calling '{self._base_url}{path}': {exc}") from exc


class OrderValidationHttpClient(_BaseHttpClient, IOrderValidationClient):
    """Fetch order snapshots from order-service."""

    async def get_order(self, order_id: UUID) -> OrderSnapshotDTO:
        """Get order snapshot by id."""
        response = await self._request("GET", f"/api/v1/orders/{order_id}")
        if response.status_code == HTTP_NOT_FOUND:
            raise LookupError(f"order '{order_id}' not found")
        if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
            raise RuntimeError("order service is unavailable")
        if response.status_code >= HTTP_BAD_REQUEST:
            raise RuntimeError("order validation request rejected")

        payload = response.json()
        return OrderSnapshotDTO(
            order_id=UUID(str(payload["id"])),
            user_id=UUID(str(payload["user_id"])),
            restaurant_id=UUID(str(payload["restaurant_id"])),
            status=str(payload["status"]),
        )


class DeliveryValidationHttpClient(_BaseHttpClient, IDeliveryValidationClient):
    """Fetch delivery snapshots from delivery-service."""

    async def get_delivery(self, order_id: UUID) -> DeliverySnapshotDTO:
        """Get delivery snapshot by order id."""
        response = await self._request("GET", f"/api/v1/deliveries/orders/{order_id}")
        if response.status_code == HTTP_NOT_FOUND:
            raise LookupError(f"delivery for order '{order_id}' not found")
        if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
            raise RuntimeError("delivery service is unavailable")
        if response.status_code >= HTTP_BAD_REQUEST:
            raise RuntimeError("delivery validation request rejected")

        payload = response.json()
        return DeliverySnapshotDTO(
            assignment_id=UUID(str(payload["assignment_id"])),
            order_id=UUID(str(payload["order_id"])),
            restaurant_id=UUID(str(payload["restaurant_id"])),
            courier_id=UUID(str(payload["courier_id"])),
            status=str(payload["status"]),
            delivered_at=payload.get("delivered_at"),
        )
