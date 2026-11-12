from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.infrastructure.jwt_service import JwtTokenService
from auth.infrastructure.password_hasher import Argon2PasswordHasher
from auth.infrastructure.refresh_token_service import OpaqueRefreshTokenService
from auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from auth.infrastructure.security_logger import LoggingSecurityEventLogger
from auth.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from auth.use_cases.login_user import LoginUser
from auth.use_cases.logout import Logout
from auth.use_cases.purge_expired_tokens import PurgeExpiredTokens
from auth.use_cases.refresh_session import RefreshSession
from auth.use_cases.register_user import RegisterUser
from core.database import get_session
from core.settings import Settings, get_settings
from users.domain.repositories import UserRepository
from users.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository,
)


def get_register_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RegisterUser:
    repository: UserRepository = SqlAlchemyUserRepository(session)
    password_hasher = Argon2PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )
    return RegisterUser(repository, password_hasher)


def get_login_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginUser:
    repository: UserRepository = SqlAlchemyUserRepository(session)
    refresh_token_repository = SqlAlchemyRefreshTokenRepository(session)
    password_hasher = Argon2PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )
    token_service = JwtTokenService(settings)
    refresh_token_service = OpaqueRefreshTokenService()
    unit_of_work = SqlAlchemyUnitOfWork(session)
    access_token_ttl_seconds = settings.access_token_ttl_minutes * 60
    return LoginUser(
        user_repository=repository,
        refresh_token_repository=refresh_token_repository,
        password_hasher=password_hasher,
        dummy_password_hash=settings.dummy_password_hash,
        token_service=token_service,
        refresh_token_service=refresh_token_service,
        unit_of_work=unit_of_work,
        access_token_ttl_seconds=access_token_ttl_seconds,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )


def get_refresh_session(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshSession:
    """Build the refresh-session use case with request-scoped persistence."""
    return RefreshSession(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        refresh_token_service=OpaqueRefreshTokenService(),
        token_service=JwtTokenService(settings),
        security_event_logger=LoggingSecurityEventLogger(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        access_token_ttl_seconds=settings.access_token_ttl_minutes * 60,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )


def get_logout(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Logout:
    """Build the logout use case with request-scoped persistence."""
    return Logout(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        refresh_token_service=OpaqueRefreshTokenService(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
    )


def get_purge_expired_tokens(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PurgeExpiredTokens:
    """Build the cleanup use case for scheduled application jobs."""
    return PurgeExpiredTokens(
        refresh_token_repository=SqlAlchemyRefreshTokenRepository(session),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        revoked_token_retention_days=settings.revoked_refresh_token_retention_days,
    )
