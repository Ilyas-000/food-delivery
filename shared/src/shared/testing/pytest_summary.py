from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from io import StringIO
import time
from typing import Any, Protocol, cast

import pytest


@dataclass
class _RunStats:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    errors: int = 0
    started_at: float = 0.0


_STATS = _RunStats()
_COVERAGE_RED_THRESHOLD = 50.0
_COVERAGE_YELLOW_THRESHOLD = 70.0


class _CovController(Protocol):
    def summary(self, stream: Any) -> float:
        ...


class _CovPlugin(Protocol):
    options: Any
    cov_report: StringIO
    cov_total: float | None
    cov_controller: _CovController | None


def pytest_configure(config: pytest.Config) -> None:
    _STATS.started_at = time.perf_counter()
    cov_plugin = _get_cov_plugin(config)
    if cov_plugin is not None:
        options = getattr(cov_plugin, "options", None)
        if options is not None:
            options.cov_report = ["term"]
    terminalreporter = config.pluginmanager.getplugin("terminalreporter")
    if terminalreporter is not None:
        terminalreporter.short_test_summary = lambda: None
        terminalreporter.summary_stats = lambda: None


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call":
        if report.outcome == "failed":
            _STATS.errors += 1
        return

    if report.outcome == "passed":
        if getattr(report, "wasxfail", False):
            _STATS.xpassed += 1
        else:
            _STATS.passed += 1
    elif report.outcome == "skipped":
        if getattr(report, "wasxfail", False):
            _STATS.xfailed += 1
        else:
            _STATS.skipped += 1
    elif report.outcome == "failed":
        _STATS.failed += 1


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # type: ignore[misc]
def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    config: pytest.Config,
) -> Generator[None, None, None]:
    cov_plugin = _get_cov_plugin(config)
    if cov_plugin is not None and hasattr(cov_plugin, "cov_report"):
        cov_plugin.cov_report = StringIO()
    terminalreporter.short_test_summary = lambda: None
    yield
    duration = time.perf_counter() - _STATS.started_at
    cov_total = _get_coverage_total(config)
    _render_summary(terminalreporter, duration, cov_total)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)  # type: ignore[misc]
def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> Generator[None, None, None]:
    terminalreporter = session.config.pluginmanager.getplugin("terminalreporter")
    if terminalreporter is not None:
        terminalreporter.summary_stats = lambda: None
    _ = exitstatus
    yield


def _get_coverage_total(config: pytest.Config) -> float | None:
    cov_plugin = _get_cov_plugin(config)
    if cov_plugin is None:
        return None
    cov_total = getattr(cov_plugin, "cov_total", None)
    if cov_total is None:
        cov_controller = getattr(cov_plugin, "cov_controller", None)
        if cov_controller is None:
            return None
        try:
            cov_total = cov_controller.summary(_NullWriter())
            if hasattr(cov_plugin, "cov_total"):
                cov_plugin.cov_total = cov_total
        except Exception:
            return None
    return float(cov_total)


def _get_cov_plugin(config: pytest.Config) -> _CovPlugin | None:
    plugin = (
        config.pluginmanager.getplugin("_cov")
        or config.pluginmanager.getplugin("cov")
        or config.pluginmanager.getplugin("pytest_cov")
    )
    if plugin is None:
        return None
    return cast(_CovPlugin, plugin)


def _render_summary(
    terminalreporter: pytest.TerminalReporter,
    duration: float,
    coverage: float | None,
) -> None:
    failed_total = _STATS.failed + _STATS.errors + _STATS.xpassed
    skipped_total = _STATS.skipped + _STATS.xfailed

    def write_line(line: str = "", **markup: bool) -> None:
        terminalreporter.write(f"{line}\n", **markup)

    header_markup = {"red": failed_total > 0, "green": failed_total == 0, "bold": True}
    write_line("")
    write_line("==================== TEST RESULTS ====================", **header_markup)
    write_line("")
    write_line(f"✅ Tests:       {_STATS.passed} passed", green=True, bold=True)
    write_line(
        f"❌ Failed:      {failed_total}",
        red=failed_total > 0,
        green=failed_total == 0,
        bold=True,
    )
    write_line(
        f"⏭️ Skipped:     {skipped_total}",
        yellow=skipped_total > 0,
        bold=skipped_total > 0,
    )
    write_line(f"⏱️ Duration:    {duration:.2f}s", cyan=True)
    write_line("")
    write_line("--------------------- COVERAGE -----------------------", cyan=True, bold=True)
    write_line("")
    if coverage is None:
        write_line("📊 Coverage:    N/A", yellow=True)
    else:
        if coverage < _COVERAGE_RED_THRESHOLD:
            coverage_markup = {"red": True, "bold": True}
        elif coverage < _COVERAGE_YELLOW_THRESHOLD:
            coverage_markup = {"yellow": True, "bold": True}
        else:
            coverage_markup = {"green": True, "bold": True}
        write_line(f"📊 Coverage:    {coverage:.1f}%", **coverage_markup)
    write_line("")
    write_line("======================================================", **header_markup)


class _NullWriter:
    def write(self, _text: str) -> None:
        return None
