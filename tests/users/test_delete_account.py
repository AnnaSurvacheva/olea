"""Integration test for the DeleteAccount use case (needs PostgreSQL)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from answers.infrastructure.model import AnswerModel
from questions.infrastructure.models import QuestionModel
from users.infrastructure.models import UsersModel
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from users.use_cases.delete_account import DeleteAccount


async def count_answers(session: AsyncSession, user_id: int) -> int:
    statement = select(func.count()).select_from(AnswerModel)
    statement = statement.where(AnswerModel.user_id == user_id)
    result = await session.scalar(statement)
    return result or 0


async def test_delete_account_removes_user_and_related_data(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            UsersModel(id=1, email="anna@example.com", role="user"),
            UsersModel(id=2, email="other@example.com", role="user"),
            QuestionModel(
                id=1,
                question="What made you happy today?",
                for_day=date.today(),
            ),
        ]
    )
    await session.flush()
    session.add_all(
        [
            AnswerModel(user_id=1, question_id=1, text="A walk in the park"),
            AnswerModel(user_id=1, question_id=1, text="A good book"),
            AnswerModel(user_id=2, question_id=1, text="A call with a friend"),
        ]
    )
    await session.commit()

    use_case = DeleteAccount(SqlAlchemyUserRepository(session))
    await use_case.execute(1)

    session.expunge_all()
    assert await session.get(UsersModel, 1) is None
    assert await count_answers(session, user_id=1) == 0
    assert await session.get(UsersModel, 2) is not None
    assert await count_answers(session, user_id=2) == 1
    assert await session.get(QuestionModel, 1) is not None
