"""Repository contract for question storage."""

from datetime import date
from typing import Protocol

from questions.domain.entities.question import Question


class QuestionRepository(Protocol):
    async def create(self, question: str, for_day: date) -> Question:
        """Save and return a question assigned to ``for_day``."""
        ...

    async def get_for_day(self, for_day: date) -> Question | None:
        """Return the question scheduled for a date, if any."""
        ...

    async def get_all_questions(self) -> list[Question]:
        """Return all questions in stable order."""
        ...
