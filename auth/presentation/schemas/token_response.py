from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    """HTTP response containing the newly issued token pair."""

    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(
        description="JWT access token.",
    )
    refresh_token: str = Field(
        description="Opaque refresh token. Store securely; it is shown only once.",
    )
    token_type: str = Field(
        default="Bearer",
        description="Authentication scheme.",
    )
    expires_in: int = Field(
        description="Access token lifetime in seconds.",
    )