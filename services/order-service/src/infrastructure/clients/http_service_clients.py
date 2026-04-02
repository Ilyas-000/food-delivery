"""HTTP client implementations for external saga dependencies."""

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import httpx

from src.application.interfaces.external_clients import (
    IDeliveryServiceClient,
    IPaymentServiceClient,
    IRestaurantServiceClient,
)
from src.domain.exceptions.order import InvalidOrderDataError
from src.domain.value_objects.order_item import OrderItem

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_INTERNAL_SERVER_ERROR = 500


class _BaseHttpServiceClient:
    """Shared low-level HTTP call helper."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                return await client.request(
                    method=method,
                    url=path,
                    json=json_body,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"request timeout calling '{self._base_url}{path}'") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"request error calling '{self._base_url}{path}': {exc}") from exc


class RestaurantServiceHttpClient(_BaseHttpServiceClient, IRestaurantServiceClient):
    """Restaurant service client used for menu item validation."""

    async def validate_items(self, restaurant_id: UUID, items: tuple[OrderItem, ...]) -> None:
        """Validate item availability and prices against restaurant service."""
        for item in items:
            path = f"/api/v1/restaurants/{restaurant_id}/menu-items/{item.menu_item_id}"
            response = await self._request("GET", path)

            if response.status_code == HTTP_NOT_FOUND:
                raise InvalidOrderDataError(
                    "menu item "
                    f"'{item.menu_item_id}' does not exist for restaurant '{restaurant_id}'"
                )
            if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
                raise RuntimeError("restaurant service is unavailable")
            if response.status_code >= HTTP_BAD_REQUEST:
                raise InvalidOrderDataError("menu validation request rejected")

            payload = response.json()
            availability = str(payload.get("availability", ""))
            if availability != "available":
                raise InvalidOrderDataError(
                    f"menu item '{item.menu_item_id}' is not available for ordering"
                )

            price_amount = _read_decimal(payload, "price_amount")
            price_currency = str(payload.get("price_currency", ""))
            if price_amount != item.unit_price or price_currency != item.currency:
                raise InvalidOrderDataError(
                    f"menu item '{item.menu_item_id}' has outdated price in request"
                )


class PaymentServiceHttpClient(_BaseHttpServiceClient, IPaymentServiceClient):
    """Payment service client for reserve/release operations."""

    async def reserve(self, order_id: UUID, user_id: UUID, amount: Decimal, currency: str) -> str:
        """Reserve funds for an order and return reservation id."""
        response = await self._request(
            "POST",
            "/api/v1/payments/reservations",
            json_body={
                "order_id": str(order_id),
                "user_id": str(user_id),
                "amount": str(amount),
                "currency": currency,
            },
            headers={"Idempotency-Key": str(order_id)},
        )

        if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
            raise RuntimeError("payment service is unavailable")
        if response.status_code >= HTTP_BAD_REQUEST:
            raise InvalidOrderDataError("payment reservation rejected")

        payload = response.json()
        reservation_id = payload.get("reservation_id") or payload.get("id")
        if reservation_id is None:
            raise RuntimeError("payment service response does not contain reservation id")
        return str(reservation_id)

    async def release(self, reservation_id: str) -> None:
        """Release reserved payment funds."""
        response = await self._request("DELETE", f"/api/v1/payments/reservations/{reservation_id}")
        if response.status_code in {HTTP_NOT_FOUND, HTTP_CONFLICT}:
            return
        if response.status_code >= HTTP_BAD_REQUEST:
            raise RuntimeError(
                f"payment reservation release failed for '{reservation_id}', "
                f"status={response.status_code}"
            )


class DeliveryServiceHttpClient(_BaseHttpServiceClient, IDeliveryServiceClient):
    """Delivery service client for courier assignment operations."""

    async def assign(self, order_id: UUID, restaurant_id: UUID) -> str:
        """Assign courier for order and return assignment id."""
        response = await self._request(
            "POST",
            "/api/v1/deliveries/assignments",
            json_body={
                "order_id": str(order_id),
                "restaurant_id": str(restaurant_id),
            },
        )

        if response.status_code >= HTTP_INTERNAL_SERVER_ERROR:
            raise RuntimeError("delivery service is unavailable")
        if response.status_code >= HTTP_BAD_REQUEST:
            raise InvalidOrderDataError("courier assignment rejected")

        payload = response.json()
        assignment_id = payload.get("assignment_id") or payload.get("id")
        if assignment_id is None:
            raise RuntimeError("delivery service response does not contain assignment id")
        return str(assignment_id)

    async def cancel(self, assignment_id: str) -> None:
        """Cancel assigned courier."""
        response = await self._request("DELETE", f"/api/v1/deliveries/assignments/{assignment_id}")
        if response.status_code in {HTTP_NOT_FOUND, HTTP_CONFLICT}:
            return
        if response.status_code >= HTTP_BAD_REQUEST:
            raise RuntimeError(
                f"courier assignment cancellation failed for '{assignment_id}', "
                f"status={response.status_code}"
            )


def _read_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    """Read decimal field from JSON payload."""
    value = payload.get(field_name)
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid '{field_name}' value in upstream response") from exc
