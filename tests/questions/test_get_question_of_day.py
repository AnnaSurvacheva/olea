import asyncio
from datetime import UTC, date, datetime

import pytest

from questions.domain.entities.question import Question
from questions.use_cases.get_question_of_day import (
    GetQuestionOfDay,
    NoQuestionScheduled,
)


class InMemoryQuestionRepository:
    def __init__(self, questions: list[Question]) -> None:
        self.questions = questions

    async def create(self, question: str, for_day: date) -> Question:
        raise NotImplementedError

    async def get_for_day(self, for_day: date) -> Question | None:
        return next(
            (question for question in self.questions if question.for_day == for_day),
            None,
        )

    async def get_all_questions(self) -> list[Question]:
        return self.questions


def make_questions(count: int) -> list[Question]:
    return [
        Question(
            id=index,
            question=f"Question {index}",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            for_day=date(2026, 11, index),
        )
        for index in range(1, count + 1)
    ]


@pytest.mark.parametrize(
    ("timezone_name", "instant", "expected_question_id"),
    [
        ("UTC", datetime(2026, 11, 6, 12, tzinfo=UTC), 6),
        (
            "Asia/Tokyo",
            datetime(2026, 11, 6, 16, tzinfo=UTC),
            7,
        ),
    ],
)
def test_question_selection_uses_users_local_date(
    timezone_name: str,
    instant: datetime,
    expected_question_id: int,
) -> None:
    use_case = GetQuestionOfDay(InMemoryQuestionRepository(make_questions(7)))

    question = asyncio.run(use_case.execute(timezone_name, now=instant))

    assert question.id == expected_question_id


def test_question_stays_the_same_during_the_local_day() -> None:
    use_case = GetQuestionOfDay(InMemoryQuestionRepository(make_questions(7)))

    morning = asyncio.run(
        use_case.execute(
            "Europe/Moscow",
            now=datetime(2026, 11, 6, 6, tzinfo=UTC),
        )
    )
    evening = asyncio.run(
        use_case.execute(
            "Europe/Moscow",
            now=datetime(2026, 11, 6, 18, tzinfo=UTC),
        )
    )

    assert morning.id == evening.id


def test_question_changes_on_the_next_local_day() -> None:
    use_case = GetQuestionOfDay(InMemoryQuestionRepository(make_questions(7)))

    today = asyncio.run(
        use_case.execute(
            "Europe/Moscow",
            now=datetime(2026, 11, 6, 20, tzinfo=UTC),
        )
    )
    tomorrow = asyncio.run(
        use_case.execute(
            "Europe/Moscow",
            now=datetime(2026, 11, 6, 21, tzinfo=UTC),
        )
    )

    assert tomorrow.id != today.id


def test_missing_scheduled_question_raises_clear_error() -> None:
    use_case = GetQuestionOfDay(InMemoryQuestionRepository([]))

    with pytest.raises(NoQuestionScheduled):
        asyncio.run(use_case.execute("UTC"))
