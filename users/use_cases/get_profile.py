"""Use case: get a user profile."""

from users.domain.entities.user import User
from users.domain.exceptions import UserNotFound
from users.domain.repositories import UserRepository


class GetProfile:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user_id: int) -> User:
        """Return the user or raise UserNotFound."""
        user = await self.repository.get(user_id)
        if user is None:
            raise UserNotFound(user_id)
        return user
