"""
User profile routes.

Endpoints:
- GET /api/v1/users/me
- PATCH /api/v1/users/me
- GET /api/v1/users/{user_id} (admin only)
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
import structlog

from src.application.dto.user import GetUserProfileDTO, UpdateUserProfileDTO
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.update_user_profile import UpdateUserProfileUseCase
from src.domain.entities.user import User
from src.domain.exceptions.base import PermissionDeniedError
from src.interface.api.v1.schemas.users import UpdateProfileRequest, UserResponse
from src.interface.dependencies.auth import get_current_user
from src.interface.dependencies.user import (
    get_update_user_profile_use_case,
    get_user_profile_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetUserProfileUseCase, Depends(get_user_profile_use_case)],
) -> UserResponse:
    """Return profile for currently authenticated user."""
    logger.info("users.me.get.started", user_id=str(current_user.id))

    dto = GetUserProfileDTO(user_id=current_user.id)
    result_dto = await use_case.execute(dto)

    logger.info("users.me.get.success", user_id=str(current_user.id))
    return UserResponse.from_dto(result_dto)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_my_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        UpdateUserProfileUseCase,
        Depends(get_update_user_profile_use_case),
    ],
) -> UserResponse:
    """Update profile for currently authenticated user."""
    logger.info("users.me.patch.started", user_id=str(current_user.id))

    dto = UpdateUserProfileDTO(
        user_id=current_user.id,
        full_name=request.full_name,
        phone=request.phone,
    )
    result_dto = await use_case.execute(dto)

    logger.info("users.me.patch.success", user_id=str(current_user.id))
    return UserResponse.from_dto(result_dto)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by id (admin only)",
)
async def get_user_profile_by_id(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetUserProfileUseCase, Depends(get_user_profile_use_case)],
) -> UserResponse:
    """Return profile by id for admins."""
    if "manage_users" not in current_user.role.permissions:
        raise PermissionDeniedError("Admin permissions required")

    logger.info(
        "users.admin.get.started",
        requested_user_id=str(user_id),
        admin_user_id=str(current_user.id),
    )

    dto = GetUserProfileDTO(user_id=user_id)
    result_dto = await use_case.execute(dto)

    logger.info(
        "users.admin.get.success",
        requested_user_id=str(user_id),
        admin_user_id=str(current_user.id),
    )
    return UserResponse.from_dto(result_dto)
