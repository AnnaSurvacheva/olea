"""SQLAlchemy transaction boundary for authentication use cases."""

from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.ports import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Commit or roll back work performed through a shared async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind transaction control to the request-scoped async session."""
        self._session = session

    async def commit(self) -> None:
        """Commit the active SQLAlchemy session transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the active SQLAlchemy session transaction."""
        await self._session.rollback()
