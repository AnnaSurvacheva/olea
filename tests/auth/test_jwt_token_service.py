from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from pydantic import SecretStr

from auth.domain.exceptions import InvalidToken
from auth.infrastructure.jwt_service import (
    JWT_ALGORITHM,
    JwtTokenService,
)
from core.settings import Settings


def test_issue_access_contains_expected_claims_and_ttl() -> None:
    ttl_minutes = 15
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        jwt_issuer="test-app",
        access_token_ttl_minutes=ttl_minutes,
        dummy_password_hash="dummy-hash",
    )
    service = JwtTokenService(settings)

    token = service.issue_access(user_id=42)

    claims = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        issuer=settings.jwt_issuer,
    )

    assert claims["sub"] == "42"
    assert claims["iss"] == "test-app"
    assert claims["typ"] == "access"
    assert claims["exp"] - claims["iat"] == ttl_minutes * 60

    # Если jti — некорректный UUID, UUID(...) выбросит ValueError.
    UUID(claims["jti"])


def test_each_access_token_has_unique_jti() -> None:
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        jwt_issuer="test-app",
        access_token_ttl_minutes=15,
        dummy_password_hash="dummy-hash",
    )
    service = JwtTokenService(settings)
    secret = settings.jwt_secret_key.get_secret_value()

    first = jwt.decode(
        service.issue_access(42),
        secret,
        algorithms=[JWT_ALGORITHM],
        issuer=settings.jwt_issuer,
    )
    second = jwt.decode(
        service.issue_access(42),
        secret,
        algorithms=[JWT_ALGORITHM],
        issuer=settings.jwt_issuer,
    )

    assert first["jti"] != second["jti"]


@pytest.mark.parametrize(
    "claims",
    [
        {
            "sub": "42",
            "iss": "test-app",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) - timedelta(minutes=1),
            "jti": "expired-token",
            "typ": "access",
        },
        {
            "sub": "42",
            "iss": "another-app",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=1),
            "jti": "foreign-issuer",
            "typ": "access",
        },
        {
            "sub": "42",
            "iss": "test-app",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=1),
            "jti": "wrong-type",
            "typ": "refresh",
        },
    ],
)
def test_decode_rejects_expired_foreign_issuer_and_wrong_type(
    claims: dict[str, str | datetime],
) -> None:
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        jwt_issuer="test-app",
        access_token_ttl_minutes=15,
        dummy_password_hash="dummy-hash",
    )
    service = JwtTokenService(settings)
    token = jwt.encode(
        claims,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(InvalidToken):
        service.decode_access(token)


def test_decode_rejects_invalid_signature() -> None:
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        jwt_issuer="test-app",
        access_token_ttl_minutes=15,
        dummy_password_hash="dummy-hash",
    )
    service = JwtTokenService(settings)
    token = JwtTokenService(
        Settings(
            jwt_secret_key=SecretStr("different-test-secret-for-unit-tests-32-bytes"),
            jwt_issuer="test-app",
            access_token_ttl_minutes=15,
            dummy_password_hash="dummy-hash",
        )
    ).issue_access(42)

    with pytest.raises(InvalidToken):
        service.decode_access(token)


def test_decode_rejects_unsigned_token() -> None:
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        jwt_issuer="test-app",
        access_token_ttl_minutes=15,
        dummy_password_hash="dummy-hash",
    )
    service = JwtTokenService(settings)
    token = jwt.encode(
        {
            "sub": "42",
            "iss": "test-app",
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(minutes=1),
            "jti": "unsigned-token",
            "typ": "access",
        },
        key="",
        algorithm="none",
    )

    with pytest.raises(InvalidToken):
        service.decode_access(token)
