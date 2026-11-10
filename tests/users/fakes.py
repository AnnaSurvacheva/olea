"""Fake objects used instead of the real database in unit tests."""

from dataclasses import replace
from datetime import UTC, datetime

from auth.domain.entities.user_credentials import UserCredentials
from users.domain.entities.user import User
from users.domain.exceptions import UserNotFound
from users.domain.repositories import UserChanges, UserRepository


class InMemoryUserRepository(UserRepository):
    """Keeps users in a dictionary instead of PostgreSQL."""

    def __init__(self, users: list[User] | None = None) -> None:
        self.users = {user.id: user for user in users or []}
        self.passwords: dict[int, str] = {}

    async def create(self, email: str, hashed_password: str, timezone: str) -> User:
        new_id = max(self.users, default=0) + 1
        user = User(
            id=new_id,
            email=email,
            display_name=None,
            timezone=timezone,
            created_at=datetime.now(UTC),
        )
        self.users[new_id] = user
        self.passwords[new_id] = hashed_password
        return user

    async def get_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def get(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def update(self, user_id: int, changes: UserChanges) -> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None
        updated = replace(user, **changes)
        self.users[user_id] = updated
        return updated

    async def delete(self, user_id: int) -> bool:
        return self.users.pop(user_id, None) is not None

    async def get_credentials_by_email(
        self,
        email: str,
    ) -> UserCredentials | None:
        for user in self.users.values():
            if user.email == email:
                return UserCredentials(
                    user=user,
                    hashed_password=self.passwords.get(user.id),
                )
        return None

    async def update_password_hash(self, user_id: int, hashed_password: str) -> None:
        if user_id not in self.users:
            raise UserNotFound(user_id)
        self.passwords[user_id] = hashed_password
