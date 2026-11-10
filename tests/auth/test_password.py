"""Unit tests for the password policy."""

import pytest

from auth.domain.exceptions import WeakPassword
from auth.domain.password import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    validate_password,
)

EMAIL = "anna@example.com"


def test_accepts_password_on_minimum_length() -> None:
    validate_password("a" * MIN_PASSWORD_LENGTH, EMAIL)


def test_accepts_password_on_maximum_length() -> None:
    validate_password("a" * MAX_PASSWORD_LENGTH, EMAIL)


def test_rejects_password_shorter_than_minimum() -> None:
    password = "a" * (MIN_PASSWORD_LENGTH - 1)

    with pytest.raises(WeakPassword) as error:
        validate_password(password, EMAIL)

    assert password not in str(error.value)
    assert str(MIN_PASSWORD_LENGTH) in error.value.reason


def test_rejects_password_longer_than_maximum() -> None:
    password = "a" * (MAX_PASSWORD_LENGTH + 1)

    with pytest.raises(WeakPassword) as error:
        validate_password(password, EMAIL)

    assert password not in str(error.value)
    assert str(MAX_PASSWORD_LENGTH) in error.value.reason


def test_rejects_password_equal_to_email_ignoring_case() -> None:
    password = "Anna@Example.COM"

    with pytest.raises(WeakPassword) as error:
        validate_password(password, EMAIL)

    assert password not in str(error.value)
    assert "must not match email" in error.value.reason


@pytest.mark.parametrize("password", ["password", "PASSWORD", "12345678"])
def test_rejects_common_passwords(password: str) -> None:
    with pytest.raises(WeakPassword) as error:
        validate_password(password, EMAIL)

    assert password not in str(error.value)
    assert "too common" in error.value.reason
