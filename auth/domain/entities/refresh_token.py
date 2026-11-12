from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RefreshToken:
    """Represent persisted refresh-token state without exposing the bearer value."""

    id: int
    user_id: int
    token_hash: str
    family_id: str
    jti: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by: str | None
    created_at: datetime


@dataclass(frozen=True)
class GeneratedRefreshToken:
    """Carry a newly generated bearer token and its database-safe digest."""

    plain_token: str = field(repr=False)
    token_hash: str
