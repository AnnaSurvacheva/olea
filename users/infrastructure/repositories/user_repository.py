"""SQLAlchemy implementation of the user repository."""

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from users.domain.entities.user import User
from users.domain.repositories import UserChanges, UserRepository
from users.infrastructure.mappers import to_entity
from users.infrastructure.models import UsersModel


class SqlAlchemyUserRepository(UserRepository):
    """Stores users in PostgreSQL and returns only domain entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    async def create(
        self, email: str, hashed_password: str, timezone: str
    ) -> User:
        """Save a new user and return it."""
        model = UsersModel(
            email=email,
            hashed_password=hashed_password,
            timezone=timezone,
            role="user",
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return to_entity(model)

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None if not found."""
        statement = select(UsersModel).where(UsersModel.email == email)
        model = await self.session.scalar(statement)
        if model is None:
            return None
        return to_entity(model)
    async def get(self, user_id: int) -> User | None:
        """Return the user with the given id, or None if not found."""
        model = await self.session.get(UsersModel, user_id)
        if model is None:
            return None
        return to_entity(model)

    async def update(self, user_id: int, changes: UserChanges) -> None | User:
        """Update only the given fields and return the updated user."""
        if not changes:
            return await self.get(user_id)
        statement = (
            update(UsersModel)
            .where(UsersModel.id == user_id)
            .values(**changes)
            .returning(UsersModel)
        )
        result = await self.session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        user = to_entity(model)
        await self.session.commit()
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete the user with one query. Return False if not found."""
        statement = (
            delete(UsersModel).where(UsersModel.id == user_id).returning(UsersModel.id)
        )
        result = await self.session.execute(statement)
        deleted_id = result.scalar_one_or_none()
        await self.session.commit()
        return deleted_id is not None
