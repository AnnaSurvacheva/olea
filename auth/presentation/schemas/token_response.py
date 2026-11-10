from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):

    model_config = ConfigDict(
        extra="forbid", 
    )
    
    access_token: str = Field(
        description="JWT access token.",
    )
    token_type: str = Field(
        default="Bearer",
        description="Authentication scheme.",
    )
    expires_in: int = Field(
        description="Access token lifetime in seconds.",
    )

    