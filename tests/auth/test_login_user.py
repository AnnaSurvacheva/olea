from datetime import UTC, datetime

import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.entities.login_result import LoginResult
from auth.domain.entities.refresh_token import GeneratedRefreshToken, RefreshToken
from auth.domain.entities.user_credentials import UserCredentials
from auth.domain.exceptions import InvalidCredentials
from auth.domain.ports import PasswordHasher, RefreshTokenService, TokenService
from auth.domain.repositories import RefreshTokenRepository
from auth.infrastructure.jwt_service import JwtTokenService
from auth.infrastructure.models import RefreshTokenModel
from auth.infrastructure.refresh_token_service import OpaqueRefreshTokenService
from auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from auth.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from auth.presentation.router import login
from auth.presentation.schemas.login_request import LoginRequest
from auth.presentation.schemas.token_response import TokenResponse
from auth.use_cases.login_user import LoginUser
from core.settings import Settings
from users.domain.entities.user import User
from users.domain.repositories import UserChanges, UserRepository
from users.infrastructure.models import UsersModel
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


class FakeUserRepository(UserRepository):
    def __init__(self, credentials: UserCredentials | None) -> None:
        """Create a user-repository fake for login tests."""
        self.credentials = credentials
        self.requested_email: str | None = None
        self.updated_password_hash: tuple[int, str] | None = None

    async def get_credentials_by_email(
        self,
        email: str,
    ) -> UserCredentials | None:
        """Return the configured user credentials."""
        self.requested_email = email
        return self.credentials

    async def update_password_hash(
        self,
        user_id: int,
        hashed_password: str,
    ) -> None:
        """Record the new hash requested by a login use case."""
        self.updated_password_hash = (user_id, hashed_password)

    async def create(self, email: str, hashed_password: str, timezone: str) -> User:
        """Reject unused user creation in login tests."""
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        """Reject unused user lookup in login tests."""
        raise NotImplementedError

    async def get(self, user_id: int) -> User | None:
        """Reject unused user lookup in login tests."""
        raise NotImplementedError

    async def update(self, user_id: int, changes: UserChanges) -> User | None:
        """Reject unused user updates in login tests."""
        raise NotImplementedError

    async def delete(self, user_id: int) -> bool:
        """Reject unused user deletion in login tests."""
        raise NotImplementedError


class FakePasswordHasher(PasswordHasher):
    def __init__(self, password_is_valid: bool, needs_rehash: bool = False) -> None:
        """Configure a deterministic password-hasher fake."""
        self.password_is_valid = password_is_valid
        self.should_rehash = needs_rehash
        self.verified_hashes: list[str] = []

    def hash(self, password: str) -> str:
        """Return a deterministic password hash."""
        return f"new-hash:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        """Return the configured verification result."""
        return self.password_is_valid

    async def verify_in_thread(self, password: str, hashed_password: str) -> bool:
        """Track the hash verified by the login use case."""
        self.verified_hashes.append(hashed_password)
        return self.password_is_valid

    def needs_rehash(self, hashed_password: str) -> bool:
        """Return the configured rehash decision."""
        return self.should_rehash

    async def hash_in_thread(self, password: str) -> str:
        """Return a deterministic replacement password hash."""
        return f"new-hash:{password}"


class FakeTokenService(TokenService):
    def __init__(self) -> None:
        """Track access-token issuance in unit tests."""
        self.issued_user_ids: list[int] = []

    def issue_access(self, user_id: int) -> str:
        """Return a deterministic token for a user."""
        self.issued_user_ids.append(user_id)
        return f"token-for:{user_id}"

    def decode_access(self, token: str) -> int:
        """Decode a deterministic test token."""
        return int(token.removeprefix("token-for:"))


class FakeRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        """Create an in-memory repository for login unit tests."""
        self.created_tokens: list[dict[str, object]] = []

    async def create(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Capture a persisted token's safe metadata for assertions."""
        self.created_tokens.append(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "family_id": family_id,
                "jti": jti,
                "expires_at": expires_at,
            }
        )
        return RefreshToken(
            id=len(self.created_tokens),
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            jti=jti,
            expires_at=expires_at,
            revoked_at=None,
            replaced_by=None,
            created_at=datetime.now(UTC),
        )

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Return no result because this fake is used only during login."""
        return None

    async def revoke(self, token_hash: str) -> bool:
        """Report that this fake did not revoke any token."""
        return False

    async def update_replaced_by(self, jti: str, replaced_by: str) -> bool:
        """Report that this fake did not link any replacement."""
        return False

    async def revoke_family(self, family_id: str) -> int:
        """Report that this fake did not revoke a family."""
        return 0

    async def delete_expired(
        self,
        expired_before: datetime,
        revoked_before: datetime,
    ) -> int:
        """Report that this fake did not delete persisted tokens."""
        return 0


class FakeRefreshTokenService(RefreshTokenService):
    def generate(self) -> GeneratedRefreshToken:
        """Return a fixed token pair for deterministic login tests."""
        return GeneratedRefreshToken(
            plain_token="opaque-refresh-token",
            token_hash="a" * 64,
        )

    def hash_token(self, plain_token: str) -> str:
        """Return the deterministic fake digest."""
        return "a" * 64


class FakeUnitOfWork:
    def __init__(self) -> None:
        """Initialize commit and rollback counters for use-case tests."""
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        """Record a transaction commit."""
        self.commit_count += 1

    async def rollback(self) -> None:
        """Record a transaction rollback."""
        self.rollback_count += 1


def make_credentials(hashed_password: str = "stored-hash") -> UserCredentials:
    """Create reusable credentials for login unit tests."""
    user = User(
        id=42,
        email="user@example.com",
        display_name=None,
        timezone="UTC",
        created_at=datetime.now(UTC),
    )
    return UserCredentials(user=user, hashed_password=hashed_password)


def make_login_use_case(
    repository: FakeUserRepository,
    password_hasher: FakePasswordHasher,
    token_service: FakeTokenService,
) -> LoginUser:
    """Build LoginUser with deterministic collaborators."""
    return LoginUser(
        user_repository=repository,
        refresh_token_repository=FakeRefreshTokenRepository(),
        password_hasher=password_hasher,
        dummy_password_hash="dummy-hash",
        token_service=token_service,
        refresh_token_service=FakeRefreshTokenService(),
        unit_of_work=FakeUnitOfWork(),
        access_token_ttl_seconds=900,
        refresh_token_ttl_days=30,
    )


@pytest.mark.asyncio
async def test_login_returns_access_token_after_validating_credentials() -> None:
    """Issue a token pair after successful authentication."""
    repository = FakeUserRepository(make_credentials())
    password_hasher = FakePasswordHasher(password_is_valid=True)
    token_service = FakeTokenService()
    use_case = make_login_use_case(repository, password_hasher, token_service)

    result = await use_case.execute("  USER@example.com ", "correct-password")

    assert repository.requested_email == "user@example.com"
    assert password_hasher.verified_hashes == ["stored-hash"]
    assert token_service.issued_user_ids == [42]
    assert result == LoginResult(
        access_token="token-for:42",
        refresh_token="opaque-refresh-token",
        expires_in=900,
    )


@pytest.mark.asyncio
async def test_login_uses_dummy_hash_and_rejects_unknown_user() -> None:
    """Use a dummy hash to reduce user-enumeration timing differences."""
    repository = FakeUserRepository(credentials=None)
    password_hasher = FakePasswordHasher(password_is_valid=False)
    token_service = FakeTokenService()
    use_case = make_login_use_case(repository, password_hasher, token_service)

    with pytest.raises(InvalidCredentials) as error:
        await use_case.execute("missing@example.com", "any-password")

    assert str(error.value) == "Invalid email or password"
    assert password_hasher.verified_hashes == ["dummy-hash"]
    assert token_service.issued_user_ids == []


@pytest.mark.asyncio
async def test_login_rejects_wrong_password_with_generic_credentials_error() -> None:
    """Reject an incorrect password with the generic login error."""
    password_hasher = FakePasswordHasher(password_is_valid=False)
    use_case = make_login_use_case(
        FakeUserRepository(make_credentials()),
        password_hasher,
        FakeTokenService(),
    )

    with pytest.raises(InvalidCredentials) as error:
        await use_case.execute("user@example.com", "wrong-password")

    assert str(error.value) == "Invalid email or password"
    assert password_hasher.verified_hashes == ["stored-hash"]


@pytest.mark.asyncio
async def test_login_rehashes_password_when_hash_is_outdated() -> None:
    """Rehash a valid password when the stored hash is outdated."""
    repository = FakeUserRepository(make_credentials())
    password_hasher = FakePasswordHasher(
        password_is_valid=True,
        needs_rehash=True,
    )
    use_case = make_login_use_case(
        repository,
        password_hasher,
        FakeTokenService(),
    )

    await use_case.execute("user@example.com", "correct-password")

    assert repository.updated_password_hash == (42, "new-hash:correct-password")


@pytest.mark.asyncio
async def test_login_route_returns_token_response() -> None:
    """Return the public token response from the login route."""

    class FakeLoginUseCase:
        email: str | None = None
        password: str | None = None

        async def execute(self, email: str, password: str) -> LoginResult:
            """Return fixed tokens while capturing route arguments."""
            self.email = email
            self.password = password
            return LoginResult(
                access_token="signed-token",
                refresh_token="opaque-refresh-token",
                expires_in=900,
            )

    use_case = FakeLoginUseCase()
    response = await login(
        LoginRequest(email="user@example.com", password=" password "),
        use_case,  # type: ignore[arg-type]
    )

    assert use_case.email == "user@example.com"
    assert use_case.password == " password "
    assert isinstance(response, TokenResponse)
    assert response.access_token == "signed-token"
    assert response.refresh_token == "opaque-refresh-token"
    assert response.token_type == "Bearer"
    assert response.expires_in == 900


@pytest.mark.integration
async def test_login_persists_only_refresh_token_hash(
    session: AsyncSession,
) -> None:
    """Persist only a digest when issuing a refresh token at login."""
    user = UsersModel(
        email="login-refresh@example.com",
        hashed_password="stored-hash",
        role="user",
    )
    session.add(user)
    await session.flush()

    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        dummy_password_hash="dummy-hash",
    )
    refresh_token_service = OpaqueRefreshTokenService()
    use_case = LoginUser(
        user_repository=SqlAlchemyUserRepository(session),
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        password_hasher=FakePasswordHasher(password_is_valid=True),
        dummy_password_hash="dummy-hash",
        token_service=JwtTokenService(settings),
        refresh_token_service=refresh_token_service,
        unit_of_work=SqlAlchemyUnitOfWork(session),
        access_token_ttl_seconds=900,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )

    result = await use_case.execute("login-refresh@example.com", "password")
    stored_token = await session.scalar(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )

    assert result.refresh_token
    assert stored_token is not None
    assert stored_token.token_hash == refresh_token_service.hash_token(
        result.refresh_token
    )
    assert stored_token.token_hash != result.refresh_token
    assert stored_token.family_id
    assert stored_token.jti
