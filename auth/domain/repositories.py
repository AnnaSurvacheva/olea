"""Repository contracts for authentication data."""

from datetime import datetime
from typing import Protocol

from auth.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    """Describes storage operations for refresh tokens."""

    async def create(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        jti: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Store a refresh-token hash and return the persisted token."""
        ...

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Find a token by digest and lock its row for the current transaction."""
        ...

    async def revoke(self, token_hash: str) -> bool:
        """Revoke one active token; return whether a row was updated."""
        ...

    async def update_replaced_by(self, jti: str, replaced_by: str) -> bool:
        """Link a revoked token to its successor JTI."""
        ...

    async def revoke_family(self, family_id: str) -> int:
        """Revoke all active tokens in a family and return the number updated."""
        ...

    async def delete_expired(
        self,
        expired_before: datetime,
        revoked_before: datetime,
    ) -> int:
        """Delete expired tokens and tokens revoked before the retention cutoff."""
        ...
