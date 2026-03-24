"""Delivery dependency providers."""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.application.use_cases.assign_courier import AssignCourierUseCase
from src.application.use_cases.cancel_assignment import CancelAssignmentUseCase
from src.infrastructure.repositories.in_memory_assignment_repository import (
    InMemoryAssignmentRepository,
)

_REPOSITORY = InMemoryAssignmentRepository()


async def get_assignment_repository() -> IAssignmentRepository:
    """Provide assignment repository implementation."""
    return _REPOSITORY


async def get_assign_courier_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> AssignCourierUseCase:
    """Provide assign courier use case."""
    return AssignCourierUseCase(repository=repository)


async def get_cancel_assignment_use_case(
    repository: Annotated[IAssignmentRepository, Depends(get_assignment_repository)],
) -> CancelAssignmentUseCase:
    """Provide cancel assignment use case."""
    return CancelAssignmentUseCase(repository=repository)
