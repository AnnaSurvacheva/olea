import asyncio
from datetime import date, datetime

from questions.domain.entities.question import Question
from questions.use_cases.create_question import CreateQuestionUseCase


class InMemoryQuestionRepository:
    def __init__(self, last_question: Question | None = None) -> None:
        self.last_question = last_question
        self.created_question: Question | None = None

    async def create(self, question: str, for_day: date) -> Question:
        self.created_question = Question(
            question=question,
            created_at=datetime(2026, 11, 7),
            for_day=for_day,
            id=1,
        )
        return self.created_question

    async def get_for_day(self, for_day: date) -> Question | None:
        return None

    async def get_all_questions(self) -> list[Question]:
        return []


def test_create_question_uses_administrator_selected_day() -> None:
    repository = InMemoryQuestionRepository()
    selected_day = date(2026, 11, 20)

    created_question = asyncio.run(
        CreateQuestionUseCase(repository).execute("Next", selected_day)
    )

    assert repository.created_question is not None
    assert repository.created_question.for_day == selected_day
    assert created_question.question == "Next"
