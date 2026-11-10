from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from questions.domain.exceptions import QuestionDateAlreadyTaken
from questions.infrastructure.repositories.question_repository import (
    SqlAlchemyQuestionRepository,
)


async def test_create_rolls_back_and_reports_duplicate_schedule_date() -> None:
    class UniqueViolation(Exception):
        constraint_name = "uq_questions_for_day"

    class FailedCommitSession:
        rollback_count = 0

        def add(self, model: object) -> None:
            pass

        async def commit(self) -> None:
            raise IntegrityError("insert", {}, UniqueViolation())

        async def rollback(self) -> None:
            self.rollback_count += 1

    session = FailedCommitSession()
    repository = SqlAlchemyQuestionRepository(session)  # type: ignore[arg-type]
    selected_day = date(2026, 11, 10)

    with pytest.raises(QuestionDateAlreadyTaken) as error:
        await repository.create("Question", selected_day)

    assert error.value.for_day == selected_day
    assert session.rollback_count == 1
