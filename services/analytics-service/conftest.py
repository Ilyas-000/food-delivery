"""Pytest hooks for analytics-service tests."""

from pathlib import Path
import sys

import pytest

shared_src = Path(__file__).resolve().parents[2] / "shared" / "src"
if shared_src.exists() and str(shared_src) not in sys.path:
    sys.path.insert(0, str(shared_src))

pytest_plugins = ["shared.testing.pytest_summary"]


def pytest_configure(config: pytest.Config) -> None:
    """Register service-specific markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (real dependencies)")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset singleton state and default test backend before each test."""
    from src.config import settings
    from src.interface.dependencies.analytics import reset_analytics_state

    monkeypatch.setattr(settings, "storage_backend", "memory")
    monkeypatch.setattr(settings, "kafka_enabled", False)
    reset_analytics_state()
