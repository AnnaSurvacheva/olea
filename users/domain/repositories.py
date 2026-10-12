"""Repository contract for the users module.

This file belongs to the domain layer, so it must not import
SQLAlchemy, FastAPI or anything from the infrastructure layer.
"""

from typing import Protocol, TypedDict

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
