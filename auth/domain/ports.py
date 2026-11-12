"""Ports: what the auth module needs from the outside world."""

from typing import Protocol

from auth.domain.entities.refresh_token import GeneratedRefreshToken


class PasswordHasher(Protocol):
    """Turns a password into a hash and checks a password against a hash."""

    def hash(self, password: str) -> str:
        """Return a hash of the password."""
        ...

    def verify(self, password: str, hash_password: str) -> bool:
        """Return True if the password matches the hash."""
        ...

    def needs_rehash(self, hash_password: str) -> bool:
        """Return True if the hash was made with outdated parameters."""
        ...

    async def hash_in_thread(self, password: str) -> str:
        """Hash in a worker thread so the event loop stays free."""
        ...

    async def verify_in_thread(self, password: str, hash_password: str) -> bool:
        """Verify in a worker thread so the event loop stays free."""
        ...


class TokenService(Protocol):
    """Issues and validates access tokens."""

    def issue_access(self, user_id: int) -> str:
        """Create an access token for a user."""
        ...

    def decode_access(self, token: str) -> int:
        """Validate a token and return its user id.

        Raises InvalidToken if the token is invalid or expired.
        """
        ...


class RefreshTokenService(Protocol):
    """Creates opaque refresh tokens and their one-way storage digests."""

    def generate(self) -> GeneratedRefreshToken:
        """Return a fresh opaque token and its SHA-256 hexadecimal digest."""
        ...

    def hash_token(self, plain_token: str) -> str:
        """Return the SHA-256 hexadecimal digest for a presented token."""
        ...


class UnitOfWork(Protocol):
    """Controls commit and rollback for one application operation."""

    async def commit(self) -> None:
        """Commit the active database transaction."""
        ...

    async def rollback(self) -> None:
        """Roll back the active database transaction."""
        ...


class SecurityEventLogger(Protocol):
    """Writes security-relevant authentication events without credentials."""

    def log_refresh_token_reuse(
        self,
        family_id: str,
        user_id: int,
        occurred_at: str,
    ) -> None:
        """Record a refresh-token reuse event without logging the token."""
        ...
