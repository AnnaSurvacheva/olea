from sqlalchemy import select


from sqlalchemy.ext.asyncio import AsyncSession


from questions.infrastructure.models import QuestionModel
from questions.presentation.schemas.question import QuestionCreate


class QuestionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, question: QuestionCreate) -> QuestionModel:
        db_question = QuestionModel(question=question.question)  # type: QuestionModel

        self.session.add(db_question)

        await self.session.commit()
        await self.session.refresh(db_question)

        return db_question

    async def get_all_question(self) -> list[QuestionModel]:
        result = await self.session.execute(select(QuestionModel))
        return list(result.scalars().all())
