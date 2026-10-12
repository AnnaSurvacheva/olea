"""Fake objects used instead of the real database in unit tests."""


from dataclasses import replace

from users.domain.entities.user import User
from users.domain.repositories import UserChanges, UserRepository


class InMemoryUserRepository(UserRepository):

    """Keeps users in a dictionary instead of PostgreSQL."""

    def __init__(self, users: list[User] | None = None):
        self.users = {user.id: user for user in users or []}


    async def get(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    
    async def update(self, user_id: int, changes: UserChanges)-> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None
        updated = replace(user, **changes)
        self.users[user_id] = updated
        return updated

    async def delete(self, user_id: int) -> bool:
        return self.users.pop(user_id, None) is not None




       
            

