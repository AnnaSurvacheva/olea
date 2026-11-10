"""Email normalization rules."""

EMAIL_MAX_LENGTH = 255


def normalize_email(email: str) -> str:
    """Return the email without surrounding spaces and in lower case."""
    return email.strip().lower()


email_normalization = normalize_email
