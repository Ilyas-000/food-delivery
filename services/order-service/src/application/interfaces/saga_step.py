"""Saga step contracts for order orchestration."""

from abc import ABC, abstractmethod

from src.application.dto.order import OrderSagaContext


class ISagaStep(ABC):
    """Contract for one saga step with compensation."""

    name: str

    @abstractmethod
    async def execute(self, context: OrderSagaContext) -> None:
        """Execute step side effect."""

    @abstractmethod
    async def compensate(self, context: OrderSagaContext) -> None:
        """Rollback side effect for previously completed step."""
