"""Remove expired and long-revoked refresh-token records."""

from datetime import UTC, datetime, timedelta

from auth.domain.ports import UnitOfWork
from auth.domain.repositories import RefreshTokenRepository


class PurgeExpiredTokens:
    """Purge refresh-token rows no longer needed for validation or replay checks."""

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        unit_of_work: UnitOfWork,
        revoked_token_retention_days: int,
    ) -> None:
        """Receive persistence, transaction, and revocation-retention policy."""
        self.refresh_token_repository = refresh_token_repository
        self.unit_of_work = unit_of_work
        self.revoked_token_retention_days = revoked_token_retention_days

    async def execute(self, now: datetime | None = None) -> int:
        """Delete expired or long-revoked rows and return the deleted row count."""
        cleanup_time = now or datetime.now(UTC)
        try:
            deleted_count = await self.refresh_token_repository.delete_expired(
                expired_before=cleanup_time,
                revoked_before=cleanup_time
                - timedelta(days=self.revoked_token_retention_days),
            )
            await self.unit_of_work.commit()
            return deleted_count
        except Exception:
            await self.unit_of_work.rollback()
            raise
