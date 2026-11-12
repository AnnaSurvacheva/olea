from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.entities.refresh_token import RefreshToken
from auth.infrastructure.models import RefreshTokenModel
from auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from users.infrastructure.models import UsersModel


async def _create_user(session: AsyncSession) -> int:
    user = UsersModel(
        email=f"{uuid4()}@example.com",
        hashed_password=None,
        role="user",
    )
    session.add(user)
    await session.flush()
    return user.id


async def _create_token(
    repository: SqlAlchemyRefreshTokenRepository,
    user_id: int,
    token_hash: str,
    family_id: str,
) -> RefreshToken:
    return await repository.create(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        jti=str(uuid4()),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )


@pytest.mark.integration
async def test_create_and_find_refresh_token_by_hash(session: AsyncSession) -> None:
    user_id = await _create_user(session)
    repository = SqlAlchemyRefreshTokenRepository(session)

    created = await _create_token(repository, user_id, "a" * 64, str(uuid4()))
    found = await repository.get_by_hash_for_update("a" * 64)

    assert found == created
    assert await repository.get_by_hash_for_update("b" * 64) is None


@pytest.mark.integration
async def test_find_by_hash_locks_row_until_transaction_ends(
    session: AsyncSession,
) -> None:
    user_id = await _create_user(session)
    repository = SqlAlchemyRefreshTokenRepository(session)
    token_hash = "c" * 64
    await _create_token(repository, user_id, token_hash, str(uuid4()))
    await session.commit()

    assert await repository.get_by_hash_for_update(token_hash) is not None
    assert session.bind is not None
    async with AsyncSession(session.bind, expire_on_commit=False) as other_session:
        statement = (
            select(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .with_for_update(nowait=True)
        )
        with pytest.raises(DBAPIError):
            await other_session.scalar(statement)
        await other_session.rollback()

        await session.commit()
        assert await other_session.scalar(statement) is not None
        await other_session.rollback()


@pytest.mark.integration
async def test_revoke_token_and_revoke_family(session: AsyncSession) -> None:
    user_id = await _create_user(session)
    repository = SqlAlchemyRefreshTokenRepository(session)
    family_id = str(uuid4())
    other_family_id = str(uuid4())
    token_to_revoke = await _create_token(repository, user_id, "d" * 64, family_id)
    family_token = await _create_token(repository, user_id, "e" * 64, family_id)
    other_token = await _create_token(repository, user_id, "f" * 64, other_family_id)

    assert await repository.revoke(token_to_revoke.token_hash) is True
    assert await repository.revoke(token_to_revoke.token_hash) is False
    assert await repository.update_replaced_by(
        token_to_revoke.jti,
        family_token.jti,
    ) is True
    assert await repository.update_replaced_by(
        token_to_revoke.jti,
        family_token.jti,
    ) is False
    assert await repository.revoke_family(family_id) == 1

    revoked_token = await session.scalar(
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token_hash == token_to_revoke.token_hash)
        .execution_options(populate_existing=True)
    )
    revoked_family_token = await session.scalar(
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token_hash == family_token.token_hash)
        .execution_options(populate_existing=True)
    )
    revoked_other_token = await session.scalar(
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token_hash == other_token.token_hash)
        .execution_options(populate_existing=True)
    )

    assert revoked_token is not None and revoked_token.revoked_at is not None
    assert revoked_family_token is not None
    assert revoked_family_token.revoked_at is not None
    assert revoked_other_token is not None and revoked_other_token.revoked_at is None
