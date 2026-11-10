"""Pydantic schemas for the registration endpoint."""

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from auth.domain.email import EMAIL_MAX_LENGTH, email_normalization
from auth.domain.password import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH

NormalizedEmail = Annotated[
    EmailStr,
    Field(max_length=EMAIL_MAX_LENGTH),
    AfterValidator(email_normalization),
]
"""Validated email, stripped and lowercased.

Matches the unique index on lower(email), so "Anna@Mail.RU" and
"anna@mail.ru" are treated as the same address.

Example:
    "  Anna@Mail.RU  " -> "anna@mail.ru"
"""


class RegisterRequest(BaseModel):
    """Data the client sends to create an account."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: NormalizedEmail
    password: str = Field(
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        pattern=r"^[!-~]+$",
    )
    timezone: str = "UTC"


class RegisterResponse(BaseModel):
    """Data returned after registration. The password is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
