from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Question:
    question: str
    created_at: datetime
    for_day: date
    id: int
