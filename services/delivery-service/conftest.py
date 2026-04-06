"""Pytest hooks for delivery-service tests."""

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
