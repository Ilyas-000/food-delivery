from typing import Any
from uuid import UUID

import pytest

from src.application.dto.auth import LogoutUserDTO
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.application.interfaces.token_service import ITokenService
from src.application.use_cases.logout_user import LogoutUserUseCase
from src.domain.exceptions.base import InvalidTokenError
from src.domain.value_objects.user_role import UserRole


class FakeTokenService(ITokenService):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def create_token_pair(
        self,
        subject: str,
        role: UserRole,
        extra_claims: dict[str, Any] | None = None,
        refresh_claims: dict[str, Any] | None = None,
    ) -> Any:  # pragma: no cover - not used
        _ = subject
        _ = role
        if extra_claims:
            _ = extra_claims
        if refresh_claims:
            _ = refresh_claims
        raise NotImplementedError

    def decode_token(self, token: str) -> dict[str, Any]:
        _ = token
        return self._payload


class FakeRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, active: set[str] | None = None) -> None:
        self.active = active if active is not None else set()
        self.deleted: list[str] = []

    async def store(self, jti: str, user_id: UUID, expires_in: int) -> None:  # pragma: no cover
        _ = jti
        _ = user_id
        _ = expires_in
        raise NotImplementedError

    async def exists(self, jti: str) -> bool:
        return jti in self.active

    async def delete(self, jti: str) -> None:
        self.active.discard(jti)
        self.deleted.append(jti)


@pytest.mark.asyncio()
async def test_logout_user_success() -> None:
    token_service = FakeTokenService(payload={"type": "refresh", "jti": "jti-1"})
    refresh_repo = FakeRefreshTokenRepository(active={"jti-1"})
    use_case = LogoutUserUseCase(token_service, refresh_repo)

    await use_case.execute(LogoutUserDTO(refresh_token="refresh-token"))

    assert refresh_repo.deleted == ["jti-1"]


@pytest.mark.asyncio()
async def test_logout_user_invalid_type() -> None:
    token_service = FakeTokenService(payload={"type": "access", "jti": "jti-1"})
    refresh_repo = FakeRefreshTokenRepository(active={"jti-1"})
    use_case = LogoutUserUseCase(token_service, refresh_repo)

    with pytest.raises(InvalidTokenError):
        await use_case.execute(LogoutUserDTO(refresh_token="refresh-token"))


@pytest.mark.asyncio()
async def test_logout_user_missing_jti() -> None:
    token_service = FakeTokenService(payload={"type": "refresh"})
    refresh_repo = FakeRefreshTokenRepository(active={"jti-1"})
    use_case = LogoutUserUseCase(token_service, refresh_repo)

    with pytest.raises(InvalidTokenError):
        await use_case.execute(LogoutUserDTO(refresh_token="refresh-token"))
