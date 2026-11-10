import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from auth.domain.exceptions import EmailAlreadyRegistered
from auth.domain.ports import PasswordHasher
from auth.use_cases.register_user import RegisterUser
from users.domain.entities.user import User
from users.domain.repositories import UserChanges, UserRepository
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.password_hashes: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def create(self, email: str, hashed_password: str, timezone: str) -> User:
        async with self._lock:
            if email in self.users:
                raise EmailAlreadyRegistered(email)

            user = User(
                id=len(self.users) + 1,
                email=email,
                display_name=None,
                timezone=timezone,
                created_at=datetime.now(UTC),
            )
            self.users[email] = user
            self.password_hashes[email] = hashed_password
            return user

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def get(self, user_id: int) -> User | None:
        return next((user for user in self.users.values() if user.id == user_id), None)

    async def update(self, user_id: int, changes: UserChanges) -> User | None:
        raise NotImplementedError

    async def delete(self, user_id: int) -> bool:
        raise NotImplementedError

    async def get_credentials_by_email(self, email: str) -> None:
        raise NotImplementedError

    async def update_password_hash(
        self,
        user_id: int,
        hashed_password: str,
    ) -> None:
        raise NotImplementedError


class FakePasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self.passwords_hashed: list[str] = []

    def hash(self, password: str) -> str:
        return f"argon2id-hash:{password}"

    def verify(self, password: str, hash_password: str) -> bool:
        return hash_password == self.hash(password)

    def needs_rehash(self, hash_password: str) -> bool:
        return False

    async def hash_in_thread(self, password: str) -> str:
        self.passwords_hashed.append(password)
        return f"argon2id-hash:{password}"

    async def verify_in_thread(self, password: str, hash_password: str) -> bool:
        return self.verify(password, hash_password)


@pytest.mark.asyncio
async def test_register_normalizes_email_hashes_password_and_uses_utc_default() -> None:
    repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    use_case = RegisterUser(repository, password_hasher)

    user = await use_case.execute("  Anna@Example.COM  ", "ValidPass1")

    assert user.email == "anna@example.com"
    assert user.timezone == "UTC"
    assert repository.password_hashes == {
        "anna@example.com": "argon2id-hash:ValidPass1"
    }
    assert password_hasher.passwords_hashed == ["ValidPass1"]
    assert not hasattr(user, "password")
    assert not hasattr(user, "hashed_password")


@pytest.mark.asyncio
async def test_parallel_registrations_only_create_one_user() -> None:
    repository = FakeUserRepository()
    use_case = RegisterUser(repository, FakePasswordHasher())

    results = await asyncio.gather(
        use_case.execute("Anna@Example.com", "ValidPass1"),
        use_case.execute("anna@example.com", "AnotherPass2"),
        return_exceptions=True,
    )

    assert len(repository.users) == 1
    assert sum(isinstance(result, User) for result in results) == 1
    assert sum(isinstance(result, EmailAlreadyRegistered) for result in results) == 1


@pytest.mark.asyncio
async def test_repository_rolls_back_email_unique_conflict() -> None:
    class UniqueViolation(Exception):
        constraint_name = "ix_users_email_lower"

    class FailedCommitSession:
        rollback_count = 0

        def add(self, model: object) -> None:
            pass

        async def commit(self) -> None:
            raise IntegrityError("insert", {}, UniqueViolation())

        async def rollback(self) -> None:
            self.rollback_count += 1

    session = FailedCommitSession()
    repository = SqlAlchemyUserRepository(session)  # type: ignore[arg-type]

    with pytest.raises(EmailAlreadyRegistered):
        await repository.create(
            "anna@example.com",
            "argon2id-hash",
            "UTC",
        )

    assert session.rollback_count == 1
