from datetime import date

from questions.domain.entities.question import Question
from questions.domain.repositories import QuestionRepository


class CreateQuestionUseCase:
    def __init__(self, repository: QuestionRepository) -> None:
        self.repository = repository

    async def execute(self, question: str, for_day: date) -> Question:
        return await self.repository.create(question, for_day)
