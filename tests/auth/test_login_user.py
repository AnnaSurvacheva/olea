from datetime import UTC, datetime

import pytest

from auth.domain.entities.login_result import LoginResult
from auth.domain.entities.user_credentials import UserCredentials
from auth.domain.exceptions import InvalidCredentials
from auth.domain.ports import PasswordHasher, TokenService
from auth.presentation.router import login
from auth.presentation.schemas.login_request import LoginRequest
from auth.presentation.schemas.token_response import TokenResponse
from auth.use_cases.login_user import LoginUser
from users.domain.entities.user import User
from users.domain.repositories import UserChanges, UserRepository


class FakeUserRepository(UserRepository):
    def __init__(self, credentials: UserCredentials | None) -> None:
        self.credentials = credentials
        self.requested_email: str | None = None
        self.updated_password_hash: tuple[int, str] | None = None

    async def get_credentials_by_email(
        self,
        email: str,
    ) -> UserCredentials | None:
        self.requested_email = email
        return self.credentials

    async def update_password_hash(
        self,
        user_id: int,
        hashed_password: str,
    ) -> None:
        self.updated_password_hash = (user_id, hashed_password)

    async def create(self, email: str, hashed_password: str, timezone: str) -> User:
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    async def get(self, user_id: int) -> User | None:
        raise NotImplementedError

    async def update(self, user_id: int, changes: UserChanges) -> User | None:
        raise NotImplementedError

    async def delete(self, user_id: int) -> bool:
        raise NotImplementedError


class FakePasswordHasher(PasswordHasher):
    def __init__(self, password_is_valid: bool, needs_rehash: bool = False) -> None:
        self.password_is_valid = password_is_valid
        self.should_rehash = needs_rehash
        self.verified_hashes: list[str] = []

    def hash(self, password: str) -> str:
        return f"new-hash:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return self.password_is_valid

    async def verify_in_thread(self, password: str, hashed_password: str) -> bool:
        self.verified_hashes.append(hashed_password)
        return self.password_is_valid

    def needs_rehash(self, hashed_password: str) -> bool:
        return self.should_rehash

    async def hash_in_thread(self, password: str) -> str:
        return f"new-hash:{password}"


class FakeTokenService(TokenService):
    def __init__(self) -> None:
        self.issued_user_ids: list[int] = []

    def issue_access(self, user_id: int) -> str:
        self.issued_user_ids.append(user_id)
        return f"token-for:{user_id}"

    def decode_access(self, token: str) -> int:
        return int(token.removeprefix("token-for:"))


def make_credentials(hashed_password: str = "stored-hash") -> UserCredentials:
    user = User(
        id=42,
        email="user@example.com",
        display_name=None,
        timezone="UTC",
        created_at=datetime.now(UTC),
    )
    return UserCredentials(user=user, hashed_password=hashed_password)


@pytest.mark.asyncio
async def test_login_returns_access_token_after_validating_credentials() -> None:
    repository = FakeUserRepository(make_credentials())
    password_hasher = FakePasswordHasher(password_is_valid=True)
    token_service = FakeTokenService()
    use_case = LoginUser(
        user_repository=repository,
        password_hasher=password_hasher,
        dummy_password_hash="dummy-hash",
        token_service=token_service,
        access_token_ttl_seconds=900,
    )

    result = await use_case.execute("  USER@example.com ", "correct-password")

    assert repository.requested_email == "user@example.com"
    assert password_hasher.verified_hashes == ["stored-hash"]
    assert token_service.issued_user_ids == [42]
    assert result == LoginResult(access_token="token-for:42", expires_in=900)


@pytest.mark.asyncio
async def test_login_uses_dummy_hash_and_rejects_unknown_user() -> None:
    repository = FakeUserRepository(credentials=None)
    password_hasher = FakePasswordHasher(password_is_valid=False)
    token_service = FakeTokenService()
    use_case = LoginUser(
        user_repository=repository,
        password_hasher=password_hasher,
        dummy_password_hash="dummy-hash",
        token_service=token_service,
        access_token_ttl_seconds=900,
    )

    with pytest.raises(InvalidCredentials) as error:
        await use_case.execute("missing@example.com", "any-password")

    assert str(error.value) == "Invalid email or password"
    assert password_hasher.verified_hashes == ["dummy-hash"]
    assert token_service.issued_user_ids == []


@pytest.mark.asyncio
async def test_login_rejects_wrong_password_with_generic_credentials_error() -> None:
    password_hasher = FakePasswordHasher(password_is_valid=False)
    use_case = LoginUser(
        user_repository=FakeUserRepository(make_credentials()),
        password_hasher=password_hasher,
        dummy_password_hash="dummy-hash",
        token_service=FakeTokenService(),
        access_token_ttl_seconds=900,
    )

    with pytest.raises(InvalidCredentials) as error:
        await use_case.execute("user@example.com", "wrong-password")

    assert str(error.value) == "Invalid email or password"
    assert password_hasher.verified_hashes == ["stored-hash"]


@pytest.mark.asyncio
async def test_login_rehashes_password_when_hash_is_outdated() -> None:
    repository = FakeUserRepository(make_credentials())
    password_hasher = FakePasswordHasher(
        password_is_valid=True,
        needs_rehash=True,
    )
    use_case = LoginUser(
        user_repository=repository,
        password_hasher=password_hasher,
        dummy_password_hash="dummy-hash",
        token_service=FakeTokenService(),
        access_token_ttl_seconds=900,
    )

    await use_case.execute("user@example.com", "correct-password")

    assert repository.updated_password_hash == (42, "new-hash:correct-password")


@pytest.mark.asyncio
async def test_login_route_returns_token_response() -> None:
    class FakeLoginUseCase:
        email: str | None = None
        password: str | None = None

        async def execute(self, email: str, password: str) -> LoginResult:
            self.email = email
            self.password = password
            return LoginResult(access_token="signed-token", expires_in=900)

    use_case = FakeLoginUseCase()
    response = await login(
        LoginRequest(email="user@example.com", password=" password "),
        use_case,  # type: ignore[arg-type]
    )

    assert use_case.email == "user@example.com"
    assert use_case.password == " password "
    assert isinstance(response, TokenResponse)
    assert response.access_token == "signed-token"
    assert response.token_type == "Bearer"
    assert response.expires_in == 900
