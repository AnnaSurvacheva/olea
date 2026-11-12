from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.exceptions import InvalidRefreshToken
from auth.infrastructure.jwt_service import JwtTokenService
from auth.infrastructure.models import RefreshTokenModel
from auth.infrastructure.refresh_token_service import OpaqueRefreshTokenService
from auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from auth.infrastructure.security_logger import LoggingSecurityEventLogger
from auth.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from auth.use_cases.refresh_session import RefreshSession
from core.settings import Settings
from users.infrastructure.models import UsersModel


def _make_use_case(session: AsyncSession) -> RefreshSession:
    """Build the application use case with PostgreSQL-backed dependencies."""
    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        dummy_password_hash="dummy-hash",
    )
    return RefreshSession(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        refresh_token_service=OpaqueRefreshTokenService(),
        token_service=JwtTokenService(settings),
        security_event_logger=LoggingSecurityEventLogger(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        access_token_ttl_seconds=settings.access_token_ttl_minutes * 60,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )


async def _create_user(session: AsyncSession) -> int:
    """Insert a test user required by the refresh-token foreign key."""
    user = UsersModel(
        email=f"{uuid4()}@example.com",
        hashed_password="stored-hash",
        role="user",
    )
    session.add(user)
    await session.flush()
    return user.id


async def _create_refresh_token(
    session: AsyncSession,
    user_id: int,
    family_id: str,
    plain_token: str,
    expires_at: datetime | None = None,
) -> RefreshTokenModel:
    """Create and return a persisted token row for integration scenarios."""
    token_service = OpaqueRefreshTokenService()
    repository = SqlAlchemyRefreshTokenRepository(session)
    token = await repository.create(
        user_id=user_id,
        token_hash=token_service.hash_token(plain_token),
        family_id=family_id,
        jti=str(uuid4()),
        expires_at=expires_at or datetime.now(UTC) + timedelta(days=30),
    )
    await session.flush()
    model = await session.get(RefreshTokenModel, token.id)
    if model is None:
        raise AssertionError("Created refresh-token row was not found")
    return model


@pytest.mark.integration
async def test_refresh_rotates_token_and_links_replacement(
    session: AsyncSession,
) -> None:
    """Rotate a valid token and verify its persisted successor link."""
    user_id = await _create_user(session)
    family_id = str(uuid4())
    old_plain_token = "old-opaque-token"
    old_record = await _create_refresh_token(
        session,
        user_id,
        family_id,
        old_plain_token,
    )
    await session.commit()

    result = await _make_use_case(session).execute(old_plain_token)

    new_record = await session.scalar(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash
            == OpaqueRefreshTokenService().hash_token(result.refresh_token)
        )
    )
    await session.refresh(old_record)

    assert result.access_token
    assert result.refresh_token != old_plain_token
    assert old_record.revoked_at is not None
    assert new_record is not None
    assert new_record.family_id == family_id
    assert old_record.replaced_by == new_record.jti
    assert new_record.token_hash != result.refresh_token


@pytest.mark.integration
async def test_unknown_refresh_token_returns_generic_authentication_error(
    session: AsyncSession,
) -> None:
    """Reject an unknown opaque value with the generic refresh error."""
    with pytest.raises(InvalidRefreshToken, match="Invalid refresh token"):
        await _make_use_case(session).execute("not-known")


@pytest.mark.integration
async def test_expired_refresh_token_returns_generic_authentication_error(
    session: AsyncSession,
) -> None:
    """Reject an expired token without revealing its stored state."""
    user_id = await _create_user(session)
    await _create_refresh_token(
        session,
        user_id,
        str(uuid4()),
        "expired-opaque-token",
        datetime.now(UTC) - timedelta(seconds=1),
    )
    await session.commit()

    with pytest.raises(InvalidRefreshToken, match="Invalid refresh token"):
        await _make_use_case(session).execute("expired-opaque-token")


@pytest.mark.integration
async def test_revoked_refresh_token_returns_generic_error_and_revokes_family(
    session: AsyncSession,
) -> None:
    """Reject replay of a revoked token and invalidate its active family."""
    user_id = await _create_user(session)
    family_id = str(uuid4())
    token_service = OpaqueRefreshTokenService()
    used_token = "revoked-opaque-token"
    active_token = "active-sibling-token"
    repository = SqlAlchemyRefreshTokenRepository(session)
    revoked_record = await _create_refresh_token(
        session,
        user_id,
        family_id,
        used_token,
    )
    active_record = await _create_refresh_token(
        session,
        user_id,
        family_id,
        active_token,
    )
    assert await repository.revoke(token_service.hash_token(used_token))
    await session.commit()

    with pytest.raises(InvalidRefreshToken, match="Invalid refresh token"):
        await _make_use_case(session).execute(used_token)

    await session.refresh(active_record)
    assert revoked_record.revoked_at is not None
    assert active_record.revoked_at is not None


@pytest.mark.integration
async def test_reuse_revokes_family_logs_safe_event_and_invalidates_successor(
    session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Detect replay and ensure family revocation and safe security logging."""
    user_id = await _create_user(session)
    family_id = str(uuid4())
    old_plain_token = "original-refresh-token"
    sibling_plain_token = "active-family-token"
    old_record = await _create_refresh_token(
        session,
        user_id,
        family_id,
        old_plain_token,
    )
    sibling_record = await _create_refresh_token(
        session,
        user_id,
        family_id,
        sibling_plain_token,
    )
    await session.commit()
    use_case = _make_use_case(session)

    rotated = await use_case.execute(old_plain_token)
    with pytest.raises(InvalidRefreshToken, match="Invalid refresh token"):
        await use_case.execute(old_plain_token)

    await session.refresh(old_record)
    await session.refresh(sibling_record)
    assert old_record.revoked_at is not None
    assert sibling_record.revoked_at is not None
    caplog_record = next(
        record
        for record in caplog.records
        if getattr(record, "security_event_type", None)
        == "refresh_token_reuse_detected"
    )
    security_fields = caplog_record.__dict__
    assert security_fields["family_id"] == family_id
    assert security_fields["user_id"] == user_id
    assert security_fields["occurred_at"]
    assert old_plain_token not in caplog_record.getMessage()
    assert rotated.refresh_token not in caplog_record.getMessage()

    with pytest.raises(InvalidRefreshToken, match="Invalid refresh token"):
        await use_case.execute(rotated.refresh_token)
