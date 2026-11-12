import pytest
from pydantic import SecretStr, ValidationError

from core.settings import Settings


def _settings(refresh_token_ttl_days: int = 30) -> Settings:
    return Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        dummy_password_hash="dummy-hash",
        refresh_token_ttl_days=refresh_token_ttl_days,
    )


def test_refresh_token_ttl_defaults_to_30_days() -> None:
    assert _settings().refresh_token_ttl_days == 30


def test_refresh_token_ttl_can_be_configured() -> None:
    assert _settings(refresh_token_ttl_days=7).refresh_token_ttl_days == 7


def test_refresh_token_ttl_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _settings(refresh_token_ttl_days=0)


def test_revoked_refresh_token_retention_defaults_to_30_days() -> None:
    assert _settings().revoked_refresh_token_retention_days == 30


def test_revoked_refresh_token_retention_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(
            jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
            dummy_password_hash="dummy-hash",
            revoked_refresh_token_retention_days=0,
        )
