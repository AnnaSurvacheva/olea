from datetime import UTC, datetime, timedelta
from uuid import uuid4

from auth.domain.email import email_normalization
from auth.domain.entities.login_result import LoginResult
from auth.domain.exceptions import InvalidCredentials
from auth.domain.ports import (
    PasswordHasher,
    RefreshTokenService,
    TokenService,
    UnitOfWork,
)
from auth.domain.repositories import RefreshTokenRepository
from users.domain.repositories import UserRepository


class LoginUser:
    """Authenticate credentials and persist a new refresh-token family."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        dummy_password_hash: str,
        token_service: TokenService,
        refresh_token_service: RefreshTokenService,
        unit_of_work: UnitOfWork,
        access_token_ttl_seconds: int,
        refresh_token_ttl_days: int,
    ) -> None:
        """Receive domain ports and policy values required for login."""
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_hasher = password_hasher
        self.dummy_password_hash = dummy_password_hash
        self.token_service = token_service
        self.refresh_token_service = refresh_token_service
        self.unit_of_work = unit_of_work
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_days = refresh_token_ttl_days

    async def execute(self, email: str, password: str) -> LoginResult:
        """Validate credentials and return an access/refresh token pair."""
        normalized_email = email_normalization(email)

        credentials = await self.user_repository.get_credentials_by_email(
            normalized_email
        )

        if credentials is None or credentials.hashed_password is None:
            await self.password_hasher.verify_in_thread(
                password,
                self.dummy_password_hash,
            )
            raise InvalidCredentials()

        password_is_valid = await self.password_hasher.verify_in_thread(
            password,
            credentials.hashed_password,
        )

        if not password_is_valid:
            raise InvalidCredentials()
        if self.password_hasher.needs_rehash(credentials.hashed_password):
            new_password_hash = await self.password_hasher.hash_in_thread(password)
            await self.user_repository.update_password_hash(
                credentials.user.id,
                new_password_hash,
            )

        access_token = self.token_service.issue_access(credentials.user.id)
        generated_refresh_token = self.refresh_token_service.generate()
        try:
            await self.refresh_token_repository.create(
                user_id=credentials.user.id,
                token_hash=generated_refresh_token.token_hash,
                family_id=str(uuid4()),
                jti=str(uuid4()),
                expires_at=datetime.now(UTC)
                + timedelta(days=self.refresh_token_ttl_days),
            )
            await self.unit_of_work.commit()
        except Exception:
            await self.unit_of_work.rollback()
            raise

        return LoginResult(
            access_token=access_token,
            refresh_token=generated_refresh_token.plain_token,
            expires_in=self.access_token_ttl_seconds,
        )
