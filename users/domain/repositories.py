"""Repository contract for the users module.

This file belongs to the domain layer, so it must not import
SQLAlchemy, FastAPI or anything from the infrastructure layer.
"""

from typing import Protocol, TypedDict

from auth.domain.entities.user_credentials import UserCredentials
from users.domain.entities.user import User


class UserChanges(TypedDict, total=False):
    """Profile fields that can be changed.

    Every key is optional: pass only the fields that should be updated.
    A missing key means "leave this field as it is".
    """

    display_name: str | None
    timezone: str


class UserRepository(Protocol):
    """Describes what any user storage must be able to do.

    Use cases depend on this protocol, not on a concrete database.
    The real implementation lives in the infrastructure layer.
    """

    async def create(self, email: str, hashed_password: str, timezone: str) -> User:
        """Save a new user and return it."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None if not found."""
        ...

    async def get(self, user_id: int) -> User | None:
        """Return the user with the given id, or None if not found."""
        ...

    async def update(self, user_id: int, changes: UserChanges) -> User | None:
        """Update only the given fields and return the updated user.

        Return None if the user does not exist.
        """
        ...

    async def delete(self, user_id: int) -> bool:
        """Delete the user.

        Return True if the user was deleted, False if not found.
        """
        ...
    async def get_credentials_by_email(
    self, email: str
    ) -> UserCredentials | None:
        """Return user credentials for the given email address.

        Returns ``None`` if no user with the specified email exists.
        """
        ...


    async def update_password_hash(
        self, user_id: int, hashed_password: str
    ) -> None:
        """Update the stored password hash for the specified user.

        The provided password must already be securely hashed.
        """
        ...