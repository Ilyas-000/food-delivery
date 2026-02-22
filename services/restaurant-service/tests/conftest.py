"""Root conftest for restaurant-service tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (require database, may be skipped)",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (require full application stack)",
    )
