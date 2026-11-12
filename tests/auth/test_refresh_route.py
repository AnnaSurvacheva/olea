import json
from datetime import UTC, datetime, timedelta
from inspect import isawaitable
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from auth.domain.exceptions import InvalidRefreshToken
from auth.infrastructure.jwt_service import JwtTokenService
from auth.infrastructure.refresh_token_service import OpaqueRefreshTokenService
from auth.infrastructure.repositories.refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from auth.infrastructure.security_logger import LoggingSecurityEventLogger
from auth.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from auth.presentation.error_handler import register_auth_error
from auth.presentation.router import refresh
from auth.presentation.schemas.refresh_request import RefreshRequest
from auth.use_cases.refresh_session import RefreshSession
from core.settings import Settings
from users.infrastructure.models import UsersModel


@pytest.mark.integration
async def test_refresh_failures_have_identical_unauthorized_responses(
    session: AsyncSession,
) -> None:
    """Map unknown, expired, and revoked tokens to the same HTTP response."""
    user = UsersModel(
        email=f"{uuid4()}@example.com",
        hashed_password="stored-hash",
        role="user",
    )
    session.add(user)
    await session.flush()

    refresh_token_service = OpaqueRefreshTokenService()
    repository = SqlAlchemyRefreshTokenRepository(session)
    expired_token = "expired-route-token"
    revoked_token = "revoked-route-token"
    revoked_record = await repository.create(
        user_id=user.id,
        token_hash=refresh_token_service.hash_token(revoked_token),
        family_id=str(uuid4()),
        jti=str(uuid4()),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    await repository.create(
        user_id=user.id,
        token_hash=refresh_token_service.hash_token(expired_token),
        family_id=str(uuid4()),
        jti=str(uuid4()),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    assert await repository.revoke(revoked_record.token_hash)
    await session.commit()

    settings = Settings(
        jwt_secret_key=SecretStr("test-secret-for-unit-tests-32-bytes"),
        dummy_password_hash="dummy-hash",
    )
    use_case = RefreshSession(
        refresh_token_repository=repository,
        refresh_token_service=refresh_token_service,
        token_service=JwtTokenService(settings),
        security_event_logger=LoggingSecurityEventLogger(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        access_token_ttl_seconds=settings.access_token_ttl_minutes * 60,
        refresh_token_ttl_days=settings.refresh_token_ttl_days,
    )
    app = FastAPI()
    register_auth_error(app)
    request = Request({"type": "http"})
    error_handler = app.exception_handlers[InvalidRefreshToken]

    async def get_response(token: str) -> tuple[int, dict[str, str]]:
        """Run the route and map its domain error through FastAPI's handler."""
        try:
            await refresh(
                RefreshRequest(refresh_token=SecretStr(token)),
                use_case,
            )
        except InvalidRefreshToken as error:
            response_or_awaitable = error_handler(request, error)
            response = (
                await response_or_awaitable
                if isawaitable(response_or_awaitable)
                else response_or_awaitable
            )
            return response.status_code, json.loads(bytes(response.body).decode())
        raise AssertionError("Invalid refresh token unexpectedly succeeded")

    responses = [
        await get_response(token)
        for token in ("unknown-route-token", expired_token, revoked_token)
    ]

    assert responses == [
        (401, {"detail": "Invalid refresh token"}),
        (401, {"detail": "Invalid refresh token"}),
        (401, {"detail": "Invalid refresh token"}),
    ]
