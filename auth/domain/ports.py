"""Ports: what the auth module needs from the outside world."""

from typing import Protocol


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
