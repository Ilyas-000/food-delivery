"""
User profile dependencies for FastAPI endpoints.
"""

from typing import Annotated

from fastapi import Depends

from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.interface.dependencies.database import get_user_repository


async def get_user_profile_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> GetUserProfileUseCase:
    """Provide GetUserProfileUseCase."""
    return GetUserProfileUseCase(user_repository=repository)


async def get_update_user_profile_use_case(
    repository: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UpdateUserProfileUseCase:
    """Provide UpdateUserProfileUseCase."""
    return UpdateUserProfileUseCase(user_repository=repository)
