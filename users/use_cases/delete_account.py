"""Use case: delete a user account."""

from users.domain.exceptions import UserNotFound
from users.domain.repositories import UserRepository


class DeleteAccount:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user_id: int):
        result = await self.repository.delete(user_id)
        if not result:
            raise UserNotFound(user_id)
