"""Dependency factories for the users endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.exceptions import InvalidToken
from auth.infrastructure.jwt_service import JwtTokenService
from core.database import get_session
from core.http_exceptions import unauthorized_credentials
from core.security import bearer_scheme
from core.settings import Settings, get_settings
from users.domain.entities.user import User
from users.domain.repositories import UserRepository
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from users.use_cases.delete_account import DeleteAccount
from users.use_cases.get_profile import GetProfile
from users.use_cases.update_profile import UpdateProfile


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise unauthorized_credentials()

    token_service = JwtTokenService(settings)

    try:
        user_id = token_service.decode_access(credentials.credentials)
    except InvalidToken as exc:
        raise unauthorized_credentials() from exc

    user = await repository.get(user_id)
    if user is None:
        raise unauthorized_credentials()

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user


def get_current_user_id(
    current_user: Annotated[User, Depends(get_current_user)],
) -> int:
    return current_user.id


def get_get_profile(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> GetProfile:
    return GetProfile(repository)


def get_update_profile(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UpdateProfile:
    return UpdateProfile(repository)


def get_delete_account(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> DeleteAccount:
    return DeleteAccount(repository)
