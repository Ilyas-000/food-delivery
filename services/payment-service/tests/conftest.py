"""Pytest configuration for payment-service tests."""

import pytest

from src.interface.dependencies.payment import reset_payment_repository

pytest_plugins = ["shared.testing.pytest_summary"]


def pytest_configure(config: pytest.Config) -> None:
    """Register markers used by this service."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")


@pytest.fixture(autouse=True)
def _reset_payment_repository_for_tests() -> None:
    """Reset in-memory payment storage before each test."""
    reset_payment_repository()
