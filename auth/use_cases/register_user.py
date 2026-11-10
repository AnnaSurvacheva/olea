from auth.domain.email import email_normalization
from auth.domain.password import validate_password
from auth.domain.ports import PasswordHasher
from users.domain.entities.user import User
from users.domain.repositories import UserRepository
from users.domain.timezones import validate_timezone


class RegisterUser:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def execute(
        self,
        email: str,
        password: str,
        timezone: str = "UTC",
    ) -> User:
        normalized_email = email_normalization(email)

        validate_password(password, normalized_email)
        validate_timezone(timezone)

        hashed_password = await self.password_hasher.hash_in_thread(password)

        return await self.user_repository.create(
            email=normalized_email,
            hashed_password=hashed_password,
            timezone=timezone,
        )
