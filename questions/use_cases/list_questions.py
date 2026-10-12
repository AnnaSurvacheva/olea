import logging


from questions.infrastructure.repositories.question_repository import QuestionRepository
from questions.infrastructure.models import QuestionModel

logger = logging.getLogger(__name__)


class ListQuestionsUseCase:
    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self):
        questions = await self.repository.get_all_question()
        if not questions:
            raise Exception("Questions not found")
        logger.info("Получено вопросов: %s", len(questions))
        return questions
