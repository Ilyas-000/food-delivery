"""Unit tests for proxy error handling."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from shared.common.jwt import create_access_token

from src.config import settings
from src.routes.proxy import _to_websocket_url, proxy_delivery_order_tracking


def _build_access_token() -> str:
    return create_access_token(
        subject="test-user-id",
        secret_key=settings.jwt_secret_key,
        extra_claims={"role": "customer", "email": "test@example.com"},
    )


@pytest.mark.unit
def test_proxy_user_service_timeout(client_with_mocks):
    """Timeouts should map to 504 responses."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 504
        data = response.json()
        assert "timeout" in data["error"]["message"].lower()


@pytest.mark.unit
def test_proxy_user_service_unavailable(client_with_mocks):
    """Connection errors should map to 502 responses."""
    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == 502
        data = response.json()
        assert "connect" in data["error"]["message"].lower()


@pytest.mark.unit
def test_proxy_payment_history_requires_jwt(client_with_mocks):
    response = client_with_mocks.get("/api/v1/payments/history")

    assert response.status_code in {401, 403}


@pytest.mark.unit
def test_proxy_payment_history_success(client_with_mocks):
    token = _build_access_token()

    def request_handler(method, url, **kwargs):
        assert method == "GET"
        assert str(url).endswith("/api/v1/payments/history")
        assert kwargs["headers"]["X-User-ID"] == "test-user-id"
        return httpx.Response(status_code=200, json={"items": [], "total": 0})

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=request_handler)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.unit
def test_proxy_analytics_overview_success(client_with_mocks):
    token = _build_access_token()

    def request_handler(method, url, **kwargs):
        assert method == "GET"
        assert str(url).endswith("/api/v1/analytics/overview")
        assert kwargs["headers"]["X-User-ID"] == "test-user-id"
        return httpx.Response(
            status_code=200,
            json={
                "total_events": 5,
                "orders_created": 2,
                "orders_confirmed": 1,
                "deliveries_assigned": 1,
                "emails_sent": 1,
                "pushes_sent": 0,
                "notifications_sent": 1,
                "gross_revenue": "900.00",
                "unique_customers": 2,
                "date_from": None,
                "date_to": None,
            },
        )

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=request_handler)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.get(
            "/api/v1/analytics/overview",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["orders_created"] == 2


@pytest.mark.unit
def test_proxy_delivery_location_requires_jwt(client_with_mocks):
    response = client_with_mocks.post(
        "/api/v1/deliveries/location",
        json={
            "order_id": "00000000-0000-0000-0000-000000000001",
            "latitude": 1.0,
            "longitude": 2.0,
        },
    )
    assert response.status_code in {401, 403}


@pytest.mark.unit
def test_proxy_delivery_location_success(client_with_mocks):
    token = _build_access_token()

    payload = {
        "order_id": "00000000-0000-0000-0000-000000000001",
        "latitude": 55.7558,
        "longitude": 37.6173,
    }

    def request_handler(method, url, **kwargs):
        assert method == "POST"
        assert str(url).endswith("/api/v1/deliveries/location")
        assert kwargs["headers"]["X-User-ID"] == "test-user-id"
        assert (
            kwargs["content"]
            == b'{"order_id":"00000000-0000-0000-0000-000000000001","latitude":55.7558,"longitude":37.6173}'
        )
        return httpx.Response(status_code=200, json={"status": "in_transit"})

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(side_effect=request_handler)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = client_with_mocks.post(
            "/api/v1/deliveries/location",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "in_transit"


@pytest.mark.unit
def test_to_websocket_url_maps_http_and_https() -> None:
    assert _to_websocket_url("http://delivery-service:8005", "/ws/orders/1").startswith(
        "ws://delivery-service:8005/ws/orders/1"
    )
    assert _to_websocket_url("https://delivery.example.com", "ws/orders/2").startswith(
        "wss://delivery.example.com/ws/orders/2"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_proxy_delivery_order_tracking_bridges_backend_websocket() -> None:
    websocket = AsyncMock()
    backend_ws = AsyncMock()

    connect_context_manager = AsyncMock()
    connect_context_manager.__aenter__.return_value = backend_ws
    connect_context_manager.__aexit__.return_value = None

    bridge_mock = AsyncMock()

    with patch("src.routes.proxy._bridge_websockets", bridge_mock):
        with patch(
            "src.routes.proxy.websockets.connect",
            return_value=connect_context_manager,
        ) as connect_mock:
            await proxy_delivery_order_tracking(websocket, "order-123")

    websocket.accept.assert_awaited_once()
    expected_backend_url = _to_websocket_url(
        settings.delivery_service_url,
        "/ws/orders/order-123",
    )
    connect_mock.assert_called_once_with(
        expected_backend_url,
        open_timeout=settings.proxy_timeout_delivery,
    )
    bridge_mock.assert_awaited_once_with(websocket, backend_ws)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_proxy_delivery_order_tracking_closes_client_on_backend_error() -> None:
    websocket = AsyncMock()

    with patch("src.routes.proxy.websockets.connect", side_effect=RuntimeError("boom")):
        await proxy_delivery_order_tracking(websocket, "order-123")

    websocket.accept.assert_awaited_once()
    websocket.close.assert_awaited_once_with(code=1011)
