"""Shared fixtures for tests that need a real database."""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from answers.infrastructure.model import AnswerModel  # noqa: F401
from auth.infrastructure.models import RefreshTokenModel  # noqa: F401
from core.database import Base
from questions.infrastructure.models import QuestionModel  # noqa: F401
from users.infrastructure.models import UsersModel  # noqa: F401

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://localhost:5432/reflection_db_test",
)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Give each test an empty database and a session connected to it."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as test_session:
        yield test_session
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()
