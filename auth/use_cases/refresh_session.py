"""Rotate refresh tokens and detect reuse of previously consumed tokens."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from auth.domain.entities.login_result import LoginResult
from auth.domain.exceptions import InvalidRefreshToken
from auth.domain.ports import (
    RefreshTokenService,
    SecurityEventLogger,
    TokenService,
    UnitOfWork,
)
from auth.domain.repositories import RefreshTokenRepository


class RefreshSession:
    """Rotate a refresh token while serializing concurrent use of its row."""

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        refresh_token_service: RefreshTokenService,
        token_service: TokenService,
        security_event_logger: SecurityEventLogger,
        unit_of_work: UnitOfWork,
        access_token_ttl_seconds: int,
        refresh_token_ttl_days: int,
    ) -> None:
        """Receive persistence, token, logging, and transaction ports."""
        self.refresh_token_repository = refresh_token_repository
        self.refresh_token_service = refresh_token_service
        self.token_service = token_service
        self.security_event_logger = security_event_logger
        self.unit_of_work = unit_of_work
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, plain_refresh_token: str) -> LoginResult:
        """Validate a refresh token, rotate it, and return a replacement pair."""
        token_hash = self.refresh_token_service.hash_token(plain_refresh_token)
        transaction_committed = False

        try:
            stored_token = await self.refresh_token_repository.get_by_hash_for_update(
                token_hash
            )
            if stored_token is None:
                raise InvalidRefreshToken()

            if stored_token.revoked_at is not None or stored_token.replaced_by is not None:
                await self.refresh_token_repository.revoke_family(
                    stored_token.family_id
                )
                await self.unit_of_work.commit()
                transaction_committed = True
                occurred_at = datetime.now(UTC).isoformat()
                self.security_event_logger.log_refresh_token_reuse(
                    family_id=stored_token.family_id,
                    user_id=stored_token.user_id,
                    occurred_at=occurred_at,
                )
                raise InvalidRefreshToken()

            now = datetime.now(UTC)
            if stored_token.expires_at <= now:
                raise InvalidRefreshToken()

            access_token = self.token_service.issue_access(stored_token.user_id)
            generated_refresh_token = self.refresh_token_service.generate()
            replacement_jti = str(uuid4())

            was_revoked = await self.refresh_token_repository.revoke(token_hash)
            if not was_revoked:
                raise InvalidRefreshToken()

            await self.refresh_token_repository.create(
                user_id=stored_token.user_id,
                token_hash=generated_refresh_token.token_hash,
                family_id=stored_token.family_id,
                jti=replacement_jti,
                expires_at=now + timedelta(days=self.refresh_token_ttl_days),
            )
            was_linked = await self.refresh_token_repository.update_replaced_by(
                stored_token.jti,
                replacement_jti,
            )
            if not was_linked:
                raise InvalidRefreshToken()

            await self.unit_of_work.commit()
            transaction_committed = True
            return LoginResult(
                access_token=access_token,
                refresh_token=generated_refresh_token.plain_token,
                expires_in=self.access_token_ttl_seconds,
            )
        except InvalidRefreshToken:
            if not transaction_committed:
                await self.unit_of_work.rollback()
            raise
        except Exception:
            await self.unit_of_work.rollback()
            raise
