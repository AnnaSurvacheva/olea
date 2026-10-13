"""Pydantic schemas for the registration endpoint."""


from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Data the client sends to create an account."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128, pattern=r"^[!-~]+$")
    timezone: str = "UTC"
class RegisterResponse(BaseModel):
    """Data returned after registration. The password is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    