from questions.infrastructure.repositories.question_repository import QuestionRepository
from questions.infrastructure.models import QuestionModel



class CreateQuestionUseCase:

    def __init__(self, repository: QuestionRepository):
        self.repository = repository

    async def execute(self, question: str) -> QuestionModel:
        return await self.repository.create(question)