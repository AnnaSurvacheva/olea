from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from questions.domain.entities.question import Question
from questions.domain.exceptions import QuestionDateAlreadyTaken
from questions.infrastructure.models import QuestionModel


class SqlAlchemyQuestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: QuestionModel) -> Question:
        return Question(
            id=model.id,
            question=model.question,
            created_at=model.created_at,
            for_day=model.for_day,
        )

    async def create(self, question: str, for_day: date) -> Question:
        db_question = QuestionModel(question=question, for_day=for_day)
        self.session.add(db_question)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            ) or getattr(exc.orig, "constraint_name", None)
            if constraint_name == "uq_questions_for_day":
                raise QuestionDateAlreadyTaken(for_day) from exc
            raise
        await self.session.refresh(db_question)

        return self._to_entity(db_question)

    async def get_for_day(self, for_day: date) -> Question | None:
        result = await self.session.scalar(
            select(QuestionModel).where(QuestionModel.for_day == for_day)
        )
        return self._to_entity(result) if result is not None else None

    async def get_all_questions(self) -> list[Question]:
        result = await self.session.scalars(
            select(QuestionModel).order_by(QuestionModel.id)
        )
        return [self._to_entity(model) for model in result.all()]
