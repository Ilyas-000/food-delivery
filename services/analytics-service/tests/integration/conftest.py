"""Integration fixtures for analytics-service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import suppress

from fastapi import FastAPI
import httpx
from httpx import ASGITransport, AsyncClient
import pytest

from src.interface.dependencies import analytics as analytics_dependencies
from src.main import create_app

CLICKHOUSE_BASE_URL = "http://clickhouse:8123"
CLICKHOUSE_DATABASE = "analytics_db"


@pytest.fixture()
async def analytics_repository(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[object]:
    """Provide real ClickHouse-backed repository for integration tests."""
    repository = analytics_dependencies._CLICKHOUSE_REPOSITORY

    monkeypatch.setattr(analytics_dependencies.settings, "storage_backend", "clickhouse")
    monkeypatch.setattr(analytics_dependencies.settings, "kafka_enabled", False)
    monkeypatch.setattr(repository, "_base_url", CLICKHOUSE_BASE_URL)
    monkeypatch.setattr(repository, "_database", CLICKHOUSE_DATABASE)
    monkeypatch.setattr(repository, "_table", "analytics_events")

    try:
        async with httpx.AsyncClient(
            base_url=CLICKHOUSE_BASE_URL,
            timeout=5.0,
            trust_env=False,
        ) as client:
            response = await client.get("/ping")
            if response.status_code != httpx.codes.OK:
                pytest.skip(f"ClickHouse ping failed: {response.status_code}")
    except Exception as exc:
        pytest.skip(f"ClickHouse unavailable for analytics integration tests: {exc}")

    try:
        await repository.start()
    except Exception as exc:
        with suppress(Exception):
            await repository.stop()
        pytest.skip(f"Failed to initialize ClickHouse repository: {exc}")

    try:
        await repository._execute(
            f"TRUNCATE TABLE IF EXISTS {CLICKHOUSE_DATABASE}.analytics_events",
        )
        yield repository
    finally:
        with suppress(Exception):
            await repository._execute(
                f"TRUNCATE TABLE IF EXISTS {CLICKHOUSE_DATABASE}.analytics_events",
            )
        await repository.stop()


@pytest.fixture()
def analytics_service_app(analytics_repository: object) -> FastAPI:
    """Create analytics-service app with real ClickHouse backend."""
    _ = analytics_repository
    return create_app()


@pytest.fixture()
async def analytics_service_client(analytics_service_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Create async HTTP client for analytics-service integration tests."""
    transport = ASGITransport(app=analytics_service_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://analytics-service",
    ) as client:
        yield client
