from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Request body for user authentication."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(description="User email address.")
    password: str = Field(description="User password.")
