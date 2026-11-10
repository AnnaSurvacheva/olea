from auth.domain.email import email_normalization
from auth.domain.entities.login_result import LoginResult
from auth.domain.exceptions import InvalidCredentials
from auth.domain.ports import PasswordHasher, TokenService
from users.domain.repositories import UserRepository


class LoginUser:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        dummy_password_hash: str,
        token_service: TokenService,
        access_token_ttl_seconds: int,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.dummy_password_hash = dummy_password_hash
        self.token_service = token_service
        self.access_token_ttl_seconds = access_token_ttl_seconds

    async def execute(self, email: str, password: str) -> LoginResult:
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

        return LoginResult(
            access_token=self.token_service.issue_access(credentials.user.id),
            expires_in=self.access_token_ttl_seconds,
        )
