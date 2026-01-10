from typing import Any
from uuid import UUID

import pytest

from src.application.dto.auth import AuthTokensDTO, RefreshTokenDTO
from src.application.interfaces.refresh_token_repository import IRefreshTokenRepository
from src.application.interfaces.token_service import ITokenService
from src.application.interfaces.user_repository import IUserRepository
from src.application.use_cases.refresh_token import RefreshTokenUseCase
from src.domain.entities.user import User
from src.domain.exceptions.base import InvalidTokenError
from src.domain.value_objects.email import Email
from src.domain.value_objects.user_role import UserRole

BCRYPT_HASH = "$2b$12$" + "a" * 53


class FakeUserRepository(IUserRepository):
    def __init__(self, users: list[User]) -> None:
        self._by_id = {user.id: user for user in users}

    async def create(self, user: User) -> User:  # pragma: no cover - not used in tests
        _ = user
        raise NotImplementedError

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:  # pragma: no cover
        _ = email
        raise NotImplementedError

    async def exists_by_email(self, email: Email) -> bool:  # pragma: no cover
        _ = email
        raise NotImplementedError

    async def update(self, user: User) -> User:  # pragma: no cover - not used in tests
        _ = user
        raise NotImplementedError

    async def delete(self, user_id: UUID) -> None:  # pragma: no cover - not used in tests
        _ = user_id
        raise NotImplementedError


class FakeTokenService(ITokenService):
    def __init__(self, payload: dict[str, Any], tokens: AuthTokensDTO) -> None:
        self._payload = payload
        self._tokens = tokens

    def create_token_pair(
        self,
        subject: str,
        role: UserRole,
        extra_claims: dict[str, Any] | None = None,
        refresh_claims: dict[str, Any] | None = None,
    ) -> AuthTokensDTO:
        _ = subject
        _ = role
        if extra_claims:
            _ = extra_claims
        if refresh_claims:
            _ = refresh_claims
        return self._tokens

    def decode_token(self, token: str) -> dict[str, Any]:
        _ = token
        return self._payload


class FakeRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, active: set[str] | None = None) -> None:
        self.active = active if active is not None else set()
        self.deleted: list[str] = []
        self.stored: list[tuple[str, UUID, int]] = []

    async def store(self, jti: str, user_id: UUID, expires_in: int) -> None:
        self.active.add(jti)
        self.stored.append((jti, user_id, expires_in))

    async def exists(self, jti: str) -> bool:
        return jti in self.active

    async def delete(self, jti: str) -> None:
        self.active.discard(jti)
        self.deleted.append(jti)


@pytest.mark.asyncio()
async def test_refresh_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    old_jti = "00000000-0000-0000-0000-000000000001"
    new_jti = "00000000-0000-0000-0000-000000000002"
    monkeypatch.setattr(
        "src.application.use_cases.refresh_token.uuid4",
        lambda: UUID(new_jti),
    )
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    refresh_repo = FakeRefreshTokenRepository(active={old_jti})
    token_service = FakeTokenService(
        payload={"sub": str(user.id), "type": "refresh", "jti": old_jti},
        tokens=AuthTokensDTO(
            access_token="new-access",
            refresh_token="new-refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        ),
    )
    use_case = RefreshTokenUseCase(repo, token_service, refresh_repo)

    result = await use_case.execute(RefreshTokenDTO(refresh_token="refresh-token"))

    assert result.access_token == "new-access"
    assert result.refresh_token == "new-refresh"
    assert refresh_repo.deleted == [old_jti]
    assert refresh_repo.stored == [(new_jti, user.id, 604800)]


@pytest.mark.asyncio()
async def test_refresh_token_invalid_type() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    refresh_repo = FakeRefreshTokenRepository(active={"jti"})
    token_service = FakeTokenService(
        payload={"sub": str(user.id), "type": "access", "jti": "jti"},
        tokens=AuthTokensDTO(
            access_token="new-access",
            refresh_token="new-refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        ),
    )
    use_case = RefreshTokenUseCase(repo, token_service, refresh_repo)

    with pytest.raises(InvalidTokenError):
        await use_case.execute(RefreshTokenDTO(refresh_token="refresh-token"))


@pytest.mark.asyncio()
async def test_refresh_token_revoked() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=BCRYPT_HASH,
        full_name="John Doe",
        role=UserRole.CUSTOMER,
    )
    repo = FakeUserRepository([user])
    refresh_repo = FakeRefreshTokenRepository(active=set())
    token_service = FakeTokenService(
        payload={"sub": str(user.id), "type": "refresh", "jti": "revoked-jti"},
        tokens=AuthTokensDTO(
            access_token="new-access",
            refresh_token="new-refresh",
            token_type="bearer",
            access_expires_in=1800,
            refresh_expires_in=604800,
        ),
    )
    use_case = RefreshTokenUseCase(repo, token_service, refresh_repo)

    with pytest.raises(InvalidTokenError):
        await use_case.execute(RefreshTokenDTO(refresh_token="refresh-token"))
