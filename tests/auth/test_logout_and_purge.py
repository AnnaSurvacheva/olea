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
from auth.presentation.router import logout
from auth.presentation.schemas.refresh_request import RefreshRequest
from auth.use_cases.logout import Logout
from auth.use_cases.purge_expired_tokens import PurgeExpiredTokens
from auth.use_cases.refresh_session import RefreshSession
from core.settings import Settings
from users.infrastructure.models import UsersModel


async def _create_user(session: AsyncSession) -> int:
    """Create a user required by refresh-token foreign keys."""
    user = UsersModel(
        email=f"{uuid4()}@example.com",
        hashed_password="stored-hash",
        role="user",
    )
    session.add(user)
    await session.flush()
    return user.id


async def _create_token(
    session: AsyncSession,
    user_id: int,
    family_id: str,
    plain_token: str,
    expires_at: datetime,
    revoked_at: datetime | None = None,
) -> RefreshTokenModel:
    """Persist a refresh-token record using only its SHA-256 digest."""
    token_service = OpaqueRefreshTokenService()
    token = RefreshTokenModel(
        user_id=user_id,
        token_hash=token_service.hash_token(plain_token),
        family_id=family_id,
        jti=str(uuid4()),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )
    session.add(token)
    await session.flush()
    return token


def _make_logout(session: AsyncSession) -> Logout:
    """Build the logout use case with PostgreSQL-backed dependencies."""
    return Logout(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        refresh_token_service=OpaqueRefreshTokenService(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
    )


@pytest.mark.integration
async def test_logout_revokes_family_refresh_fails_and_repeat_is_idempotent(
    session: AsyncSession,
) -> None:
    """Logout the presented token family and make retries safe."""
    user_id = await _create_user(session)
    family_id = str(uuid4())
    first_token = "logout-first-token"
    sibling_token = "logout-sibling-token"
    active_expiry = datetime.now(UTC) + timedelta(days=30)
    first_record = await _create_token(
        session,
        user_id,
        family_id,
        first_token,
        active_expiry,
    )
    sibling_record = await _create_token(
        session,
        user_id,
        family_id,
        sibling_token,
        active_expiry,
    )
    await session.commit()

    use_case = _make_logout(session)
    first_response = await logout(
        RefreshRequest(refresh_token=SecretStr(first_token)),
        use_case,
    )
    second_response = await logout(
        RefreshRequest(refresh_token=SecretStr(first_token)),
        use_case,
    )

    await session.refresh(first_record)
    await session.refresh(sibling_record)
    assert first_response == second_response == {"detail": "Logged out"}
    assert first_record.revoked_at is not None
    assert sibling_record.revoked_at is not None

    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        dummy_password_hash="dummy-hash",
    )
    refresh_use_case = RefreshSession(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        refresh_token_service=OpaqueRefreshTokenService(),
        token_service=JwtTokenService(settings),
        security_event_logger=LoggingSecurityEventLogger(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        access_token_ttl_seconds=settings.access_token_ttl_minutes * 60,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )
    with pytest.raises(InvalidRefreshToken):
        await refresh_use_case.execute(first_token)


@pytest.mark.integration
async def test_logout_of_unknown_token_returns_same_success_response(
    session: AsyncSession,
) -> None:
    """Avoid disclosing whether a supplied logout token exists."""
    response = await logout(
        RefreshRequest(refresh_token=SecretStr("unknown-logout-token")),
        _make_logout(session),
    )

    assert response == {"detail": "Logged out"}


@pytest.mark.integration
async def test_purge_deletes_expired_and_long_revoked_but_keeps_recent_tokens(
    session: AsyncSession,
) -> None:
    """Delete expired and old revoked rows while retaining current sessions."""
    user_id = await _create_user(session)
    now = datetime.now(UTC)
    family_id = str(uuid4())
    old_expired = await _create_token(
        session,
        user_id,
        family_id,
        "expired-purge-token",
        now - timedelta(seconds=1),
    )
    long_revoked = await _create_token(
        session,
        user_id,
        family_id,
        "old-revoked-purge-token",
        now + timedelta(days=10),
        now - timedelta(days=31),
    )
    recently_revoked = await _create_token(
        session,
        user_id,
        family_id,
        "recent-revoked-purge-token",
        now + timedelta(days=10),
        now - timedelta(days=2),
    )
    active = await _create_token(
        session,
        user_id,
        family_id,
        "active-purge-token",
        now + timedelta(days=10),
    )
    await session.commit()

    use_case = PurgeExpiredTokens(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        revoked_token_retention_days=30,
    )
    deleted_count = await use_case.execute(now=now)

    remaining_ids = set(
        (
            await session.scalars(
                select(RefreshTokenModel.id).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
        ).all()
    )
    assert deleted_count == 2
    assert old_expired.id not in remaining_ids
    assert long_revoked.id not in remaining_ids
    assert recently_revoked.id in remaining_ids
    assert active.id in remaining_ids
