"""
Authentication routes - registration, login, etc.

REST API endpoints for user authentication.

Endpoints:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login (TODO)
- POST /api/v1/auth/refresh - Refresh token (TODO)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
import structlog

from src.application.dto.user import RegisterUserDTO
from src.application.use_cases.register_user import RegisterUserUseCase
from src.interface.api.v1.schemas.auth import RegisterRequest, UserResponse
from src.interface.dependencies.database import get_register_user_use_case

# Structured logging
logger = structlog.get_logger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user in the system.

    **Requirements:**
    - Email must be unique and valid format (domain validation)
    - Password must be 8-72 characters and contain letters (domain validation)
    - Full name must be 2-100 characters (domain validation)
    - Role defaults to 'customer' if not specified

    **Returns:**
    - 201 Created: User successfully registered
    - 409 Conflict: User with this email already exists
    - 422 Unprocessable Entity: Invalid email format or validation error

    **Security:**
    - Password is hashed with bcrypt before storage
    - Password hash is never returned in response
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "role": "customer",
                        "is_active": True,
                        "phone": "+1234567890",
                        "created_at": "2024-01-08T10:30:00Z",
                        "updated_at": "2024-01-08T10:30:00Z",
                    }
                }
            },
        },
        409: {
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "CONFLICT",
                            "message": "User with email 'john.doe@example.com' already exists",
                            "details": {"email": "john.doe@example.com"},
                            "request_id": "550e8400-e29b-41d4-a716-446655440000",
                            "timestamp": "2024-01-08T10:30:00Z",
                        }
                    }
                }
            },
        },
        422: {
            "description": "Invalid email or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "BUSINESS_RULE_VIOLATION",
                            "message": (
                                "Invalid password: Password must be at least 8 characters long"
                            ),
                            "details": {"reason": "Password must be at least 8 characters long"},
                            "request_id": "550e8400-e29b-41d4-a716-446655440000",
                            "timestamp": "2024-01-08T10:30:00Z",
                        }
                    }
                }
            },
        },
    },
)
async def register_user(
    request: RegisterRequest,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
) -> UserResponse:
    """
    Register a new user.

    Flow:
    1. Pydantic validates request types only
    2. Convert Pydantic schema → DTO
    3. Execute use case (business logic)
    4. Convert DTO → Pydantic response
    5. FastAPI serializes to JSON

    Args:
        request: Registration data (validated by Pydantic)
        use_case: RegisterUserUseCase (injected by FastAPI)

    Returns:
        UserResponse: Created user data (without password!)

    Raises:
        UserAlreadyExistsError: If user with email exists (→ 409)
        InvalidEmailError: If email invalid (→ 422)
        InvalidPasswordError: If password invalid (→ 422)

    Example:
        POST /api/v1/auth/register
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }

        Response (201 Created):
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "full_name": "John Doe",
            "role": "customer",
            ...
        }
    """
    logger.info("auth.register.started", email=request.email)

    # Step 1: Convert Pydantic schema → application DTO
    # This is the boundary between API layer and application layer
    dto = RegisterUserDTO(
        email=request.email,
        password=request.password,  # Plain text, will be hashed in use case
        full_name=request.full_name,
        role=request.role,
        phone=request.phone,
    )

    # Step 2: Execute use case (business logic)
    # Use case returns UserResponseDTO
    result_dto = await use_case.execute(dto)

    logger.info(
        "auth.register.success",
        user_id=str(result_dto.id),
        email=result_dto.email,
    )

    # Step 3: Convert application DTO → Pydantic response schema
    # This is the boundary between application layer and API layer
    return UserResponse.from_dto(result_dto)
