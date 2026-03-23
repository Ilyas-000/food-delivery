"""Unit tests for order dependency providers."""

import pytest

from src.infrastructure.repositories.in_memory_order_repository import InMemoryOrderRepository
from src.interface.dependencies import order as order_dependencies


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_create_order_use_case_uses_mock_saga_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryOrderRepository()
    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "mock")

    use_case = await order_dependencies.get_create_order_use_case(repository=repository)

    step_modules = [step.__class__.__module__ for step in use_case._saga_steps]
    assert all(module == "src.infrastructure.saga.mock_steps" for module in step_modules)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_create_order_use_case_uses_http_saga_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryOrderRepository()
    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "http")

    use_case = await order_dependencies.get_create_order_use_case(repository=repository)

    step_modules = [step.__class__.__module__ for step in use_case._saga_steps]
    assert all(module == "src.infrastructure.saga.http_steps" for module in step_modules)


@pytest.mark.unit()
@pytest.mark.asyncio()
async def test_get_create_order_use_case_raises_for_unknown_saga_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryOrderRepository()
    monkeypatch.setattr(order_dependencies.settings, "saga_backend", "unknown")

    with pytest.raises(RuntimeError, match="Unsupported ORDER_SERVICE_SAGA_BACKEND"):
        await order_dependencies.get_create_order_use_case(repository=repository)
