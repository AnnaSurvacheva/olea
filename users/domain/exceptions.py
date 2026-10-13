class UserError(Exception):
    """Base error for the users module."""


class UserNotFound(UserError):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with id={user_id} not found")


class InvalidTimezone(UserError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Time zone {self.value} not found")


class InvalidCredentials(UserError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")
