import pytest
from pydantic import ValidationError

from auth.domain.email import EMAIL_MAX_LENGTH, normalize_email
from auth.presentation.schemas.register import RegisterRequest

VALID_PASSWORD = "ValidPass1"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("anna@example.com", "anna@example.com"),
        ("Anna@Example.COM", "anna@example.com"),
        ("  anna@example.com  ", "anna@example.com"),
        ("  Anna@Mail.RU  ", "anna@mail.ru"),
    ],
)
def test_normalize_email_strips_and_lowercases(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "not-an-email",
        "anna@",
        "@example.com",
        "",
        "anna example@mail.com",
    ],
)
def test_register_request_rejects_invalid_email_format(raw: str) -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(email=raw, password=VALID_PASSWORD)


def test_register_request_rejects_email_longer_than_db_column() -> None:
    local_part = "a" * (EMAIL_MAX_LENGTH)
    raw = f"{local_part}@example.com"
    assert len(raw) > EMAIL_MAX_LENGTH

    with pytest.raises(ValidationError):
        RegisterRequest(email=raw, password=VALID_PASSWORD)
