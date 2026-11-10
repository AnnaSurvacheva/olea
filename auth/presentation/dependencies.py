from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.infrastructure.jwt_service import JwtTokenService
from auth.infrastructure.password_hasher import Argon2PasswordHasher
from auth.use_cases.login_user import LoginUser
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
    password_hasher = Argon2PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )
    token_service = JwtTokenService(settings)
    access_token_ttl_seconds = settings.access_token_ttl_minutes * 60
    return LoginUser(
        user_repository=repository,
        password_hasher=password_hasher,
        dummy_password_hash=settings.dummy_password_hash,
        token_service=token_service,
        access_token_ttl_seconds=access_token_ttl_seconds,
    )
