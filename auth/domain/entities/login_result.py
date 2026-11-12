from dataclasses import dataclass


@dataclass(frozen=True)
class LoginResult:
    """Represent the token pair returned after successful authentication."""

    access_token: str
    refresh_token: str
    expires_in: int
