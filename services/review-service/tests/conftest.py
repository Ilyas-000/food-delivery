"""Pytest configuration for review-service tests."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register service markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (real dependencies)")
