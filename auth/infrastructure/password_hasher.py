"""Argon2id adapter. Hashing is CPU-heavy, so async callers use to_thread."""

import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


class Argon2PasswordHasher:
    """Implements the PasswordHasher port with Argon2id."""

    def __init__(
        self,
        time_cost: int,
        memory_cost: int,
        parallelism: int,
    ) -> None:
        self._hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )

    def hash(self, password: str) -> str:
        """Return an Argon2id hash of the password."""
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        """Return True if the password matches the hash."""
        try:
            return self._hasher.verify(hashed_password, password)
        except (InvalidHashError, VerifyMismatchError):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """Return True if the hash should be rebuilt with current parameters."""
        return self._hasher.check_needs_rehash(hashed_password)

    async def hash_in_thread(self, password: str) -> str:
        """Hash in a worker thread so the event loop stays free."""
        return await asyncio.to_thread(self.hash, password)

    async def verify_in_thread(self, password: str, hashed_password: str) -> bool:
        """Verify in a worker thread so the event loop stays free."""
        return await asyncio.to_thread(self.verify, password, hashed_password)
