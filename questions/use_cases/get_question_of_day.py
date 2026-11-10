from datetime import datetime
from zoneinfo import ZoneInfo

from questions.domain.entities.question import Question
from questions.domain.repositories import QuestionRepository


class NoQuestionScheduled(Exception):
    """Raised when no question is scheduled for the requested date."""


class GetQuestionOfDay:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(
        self, timezone: str, *, now: datetime | None = None
    ) -> Question:
        user_timezone = ZoneInfo(timezone)
        current_time = now or datetime.now(user_timezone)
        local_date = current_time.astimezone(user_timezone).date()

        question = await self.repository.get_for_day(local_date)
        if question is None:
            raise NoQuestionScheduled
        return question