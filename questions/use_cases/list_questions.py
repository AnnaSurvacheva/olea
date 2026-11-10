import logging

from questions.domain.entities.question import Question
from questions.domain.repositories import QuestionRepository

logger = logging.getLogger(__name__)


class ListQuestionsUseCase:
    def __init__(self, repository: QuestionRepository) -> None:
        self.repository = repository

    async def execute(self) -> list[Question]:
        questions = await self.repository.get_all_questions()
        logger.info("Получено вопросов: %s", len(questions))
        return questions
