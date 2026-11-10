class AuthError(Exception):
    """The base class error for the auto modele"""


class EmailAlreadyRegistered(AuthError):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} is already registered")


class WeakPassword(AuthError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Password is too weak: {reason}")


class InvalidCredentials(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InvalidToken(AuthError):
    def __init__(self) -> None:
        super().__init__("Invalid or expired access token")
