from dataclasses import dataclass

from users.domain.entities.user import User


@dataclass(frozen=True)
class UserCredentials:
    user: User
    hashed_password: str | None
