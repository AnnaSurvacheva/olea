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


