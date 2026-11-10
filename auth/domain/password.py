"""Password policy for registration."""

from auth.domain.exceptions import WeakPassword

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

COMMON_PASSWORDS = frozenset(
    {
        "password",
        "12345678",
        "qwerty..",
        "qwertyui",
        "letmein",
        "admin123",
        "iloveyou",
        "87654321",
        "QWERTY!!",
    }
)


def validate_password(password: str, email: str) -> None:
    """Raise WeakPassword if the password violates the policy.

    The exception message must not include the password itself.
    """
    length = len(password)
    if length < MIN_PASSWORD_LENGTH:
        raise WeakPassword(f"must be at least {MIN_PASSWORD_LENGTH} characters")
    if length > MAX_PASSWORD_LENGTH:
        raise WeakPassword(f"must be at most {MAX_PASSWORD_LENGTH} characters")
    if password.lower() == email.lower():
        raise WeakPassword("must not match email")
    if password.lower() in COMMON_PASSWORDS:
        raise WeakPassword("is too common")
