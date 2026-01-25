"""Tests for client IP handling."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.utils.ip import get_client_ip


def _build_app(trusted_hosts: list[str] | str) -> FastAPI:
    app = FastAPI()
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=trusted_hosts)

    @app.get("/ip")
    async def ip(request: Request) -> dict[str, str]:
        return {"client_ip": get_client_ip(request)}

    return app


def test_get_client_ip_uses_xff_when_trusted() -> None:
    app = _build_app("*")
    with TestClient(app) as client:
        response = client.get("/ip", headers={"X-Forwarded-For": "203.0.113.10"})
    assert response.status_code == 200
    assert response.json()["client_ip"] == "203.0.113.10"


def test_get_client_ip_ignores_xff_when_untrusted() -> None:
    app = _build_app("127.0.0.1")
    with TestClient(app) as client:
        response = client.get("/ip", headers={"X-Forwarded-For": "203.0.113.10"})
    assert response.status_code == 200
    assert response.json()["client_ip"] == "testclient"
