"""Generate opaque refresh-token values and their storage-safe digests."""

import hashlib
import secrets

from auth.domain.entities.refresh_token import GeneratedRefreshToken


class OpaqueRefreshTokenService:
    """Generate cryptographically random opaque refresh tokens."""

    def generate(self) -> GeneratedRefreshToken:
        """Return a URL-safe bearer token and its SHA-256 hexadecimal digest."""
        plain_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plain_token.encode("utf-8")).hexdigest()
        return GeneratedRefreshToken(
            plain_token=plain_token,
            token_hash=token_hash,
        )

    @staticmethod
    def hash_token(plain_token: str) -> str:
        """Return the SHA-256 hexadecimal digest for a presented token."""
        return hashlib.sha256(plain_token.encode("utf-8")).hexdigest()
