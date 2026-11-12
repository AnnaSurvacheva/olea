"""Request schema for refresh-token rotation."""

from pydantic import BaseModel, ConfigDict, SecretStr


class RefreshRequest(BaseModel):
    """Accept an opaque refresh token without exposing it in representations."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: SecretStr
