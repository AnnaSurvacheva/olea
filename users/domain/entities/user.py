from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: int
    email: str
    display_name: str | None
    timezone: str
    created_at: datetime
