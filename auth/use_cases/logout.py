"""Revoke a refresh-token session family on logout."""

from auth.domain.ports import RefreshTokenService, UnitOfWork
from auth.domain.repositories import RefreshTokenRepository


class Logout:
    """Revoke every token belonging to the presented refresh-token family."""

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        refresh_token_service: RefreshTokenService,
        unit_of_work: UnitOfWork,
    ) -> None:
        """Receive token, persistence, and transaction dependencies."""
        self.refresh_token_repository = refresh_token_repository
        self.refresh_token_service = refresh_token_service
        self.unit_of_work = unit_of_work

    async def execute(self, plain_refresh_token: str) -> None:
        """Log out idempotently without revealing whether a token was known."""
        token_hash = self.refresh_token_service.hash_token(plain_refresh_token)
        try:
            refresh_token = (
                await self.refresh_token_repository.get_by_hash_for_update(token_hash)
            )
            if refresh_token is not None:
                await self.refresh_token_repository.revoke_family(
                    refresh_token.family_id
                )
                await self.unit_of_work.commit()
        except Exception:
            await self.unit_of_work.rollback()
            raise
