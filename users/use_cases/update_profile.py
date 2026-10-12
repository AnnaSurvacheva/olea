"""Use case: update a user profile."""

from users.domain.entities.user import User
from users.domain.exceptions import UserNotFound
from users.domain.repositories import UserChanges, UserRepository
from users.domain.timezones import validate_timezone


class UpdateProfile:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(self, user_id: int, changes: UserChanges) -> User:
        """Apply only the given changes or raise a domain error."""
        if "timezone" in changes:
            validate_timezone(changes["timezone"])
        user = await self.repository.update(user_id, changes)
        if user is None:
            raise UserNotFound(user_id)
        return user
