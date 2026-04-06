"""Pytest hooks for order-service tests."""

from pathlib import Path
import sys

import pytest

shared_src = Path(__file__).resolve().parents[2] / "shared" / "src"
if shared_src.exists() and str(shared_src) not in sys.path:
    sys.path.insert(0, str(shared_src))

pytest_plugins = ["shared.testing.pytest_summary"]


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
def _force_mock_saga_backend_for_unit_tests(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep unit tests isolated from external HTTP saga dependencies."""
    if request.node.get_closest_marker("unit") is None:
        return

    from src.interface.dependencies import order as order_dependencies

    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "mock")
    monkeypatch.setattr(order_dependencies.settings, "repository_backend", "memory")
