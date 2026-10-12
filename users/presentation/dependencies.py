"""Dependency factories for the users endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from users.domain.repositories import UserRepository
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from users.use_cases.delete_account import DeleteAccount
from users.use_cases.get_profile import GetProfile
from users.use_cases.update_profile import UpdateProfile

STUB_USER_ID = 1


def get_current_user_id() -> int:
    """Temporary stub until real authentication (day 8)."""
    return STUB_USER_ID


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


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