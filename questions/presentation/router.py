from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from questions.domain.exceptions import QuestionDateAlreadyTaken
from questions.infrastructure.repositories.question_repository import (
    SqlAlchemyQuestionRepository,
)
from questions.presentation.schemas.question import QuestionCreate, QuestionResponse
from questions.use_cases.create_question import CreateQuestionUseCase
from questions.use_cases.get_question_of_day import (
    GetQuestionOfDay,
    NoQuestionScheduled,
)
from questions.use_cases.list_questions import ListQuestionsUseCase
from users.domain.entities.user import User
from users.presentation.dependencies import (
    get_current_admin,
    get_current_user_id,
    get_get_profile,
)
from users.use_cases.get_profile import GetProfile

router = APIRouter(prefix="/questions", tags=["Questions"])

CurrentUserId = Annotated[int, Depends(get_current_user_id)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]


@router.post("/create/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    admin: CurrentAdmin,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuestionResponse:
    repository = SqlAlchemyQuestionRepository(session)
    use_case = CreateQuestionUseCase(repository)
    try:
        created_question = await use_case.execute(
            question.question,
            question.for_day,
        )
    except QuestionDateAlreadyTaken as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return QuestionResponse.model_validate(created_question)


@router.get("/list", response_model=list[QuestionResponse])
async def list_questions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[QuestionResponse]:
    repository = SqlAlchemyQuestionRepository(session)
    use_case = ListQuestionsUseCase(repository)
    questions = await use_case.execute()
    return [QuestionResponse.model_validate(question) for question in questions]


@router.get("/today", response_model=QuestionResponse)
async def get_today_question(
    user_id: CurrentUserId,
    profile_use_case: Annotated[GetProfile, Depends(get_get_profile)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QuestionResponse:
    user = await profile_use_case.execute(user_id)
    use_case = GetQuestionOfDay(SqlAlchemyQuestionRepository(session))

    try:
        question = await use_case.execute(user.timezone)
        return QuestionResponse.model_validate(question)
    except NoQuestionScheduled as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="На сегодня вопрос не запланирован",
        ) from error
