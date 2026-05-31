"""Pytest configuration for delivery-service tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register markers used by this service."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (real dependencies)")
