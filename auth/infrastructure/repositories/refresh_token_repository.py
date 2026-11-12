from datetime import datetime

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.entities.refresh_token import RefreshToken
from auth.domain.repositories import RefreshTokenRepository
from auth.infrastructure.models import RefreshTokenModel


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    """Persists refresh-token hashes in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=model.id,
            user_id=model.user_id,
            token_hash=model.token_hash,
            family_id=model.family_id,
            jti=model.jti,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by=model.replaced_by,
            created_at=model.created_at,
        )

    async def create(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        model = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            jti=jti,
            expires_at=expires_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Find and lock a token row by its stored digest."""
        statement = (
            select(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        model = await self.session.scalar(statement)
        return self._to_entity(model) if model is not None else None

    async def update_replaced_by(self, jti: str, replaced_by: str) -> bool:
        """Set a successor JTI once on a revoked token row."""
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.jti == jti,
                RefreshTokenModel.revoked_at.is_not(None),
                RefreshTokenModel.replaced_by.is_(None),
            )
            .values(replaced_by=replaced_by)
            .returning(RefreshTokenModel.id)
        )
        return (await self.session.scalar(statement)) is not None

    async def revoke(self, token_hash: str) -> bool:
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
            .returning(RefreshTokenModel.id)
        )
        return (await self.session.scalar(statement)) is not None

    async def revoke_family(self, family_id: str) -> int:
        statement = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.family_id == family_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
            .returning(RefreshTokenModel.id)
        )
        result = await self.session.scalars(statement)
        return len(result.all())

    async def delete_expired(
        self,
        expired_before: datetime,
        revoked_before: datetime,
    ) -> int:
        """Delete expired rows and rows revoked before the retention cutoff."""
        statement = (
            delete(RefreshTokenModel)
            .where(
                or_(
                    RefreshTokenModel.expires_at <= expired_before,
                    RefreshTokenModel.revoked_at <= revoked_before,
                )
            )
            .returning(RefreshTokenModel.id)
        )
        result = await self.session.scalars(statement)
        return len(result.all())
