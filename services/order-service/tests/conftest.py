"""Pytest configuration for order-service tests."""

import pytest

from src.interface.dependencies import order as order_dependencies


def pytest_configure(config: pytest.Config) -> None:
    """Register markers used by this service."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (require database, may be skipped)",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (require full application stack)",
    )


@pytest.fixture(autouse=True)
def _force_mock_saga_backend_for_unit_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep unit tests isolated from external HTTP saga dependencies."""
    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "mock")
    monkeypatch.setattr(order_dependencies.settings, "repository_backend", "memory")
