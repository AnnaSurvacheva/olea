import hashlib

from auth.infrastructure.refresh_token_service import OpaqueRefreshTokenService


def test_generated_refresh_token_is_random_and_returns_sha256_digest() -> None:
    """Generate distinct opaque secrets and verify their SHA-256 digests."""
    service = OpaqueRefreshTokenService()

    first_token = service.generate()
    second_token = service.generate()

    assert first_token.plain_token != second_token.plain_token
    assert first_token.token_hash == hashlib.sha256(
        first_token.plain_token.encode("utf-8")
    ).hexdigest()
    assert first_token.token_hash != first_token.plain_token


def test_refresh_token_hash_is_stable() -> None:
    """Produce the same digest for the same presented token."""
    service = OpaqueRefreshTokenService()
    plain_token = "opaque-example"

    assert service.hash_token(plain_token) == hashlib.sha256(
        plain_token.encode("utf-8")
    ).hexdigest()
