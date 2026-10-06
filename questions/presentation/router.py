from fastapi import APIRouter


from questions.presentation.schemas.question import QuestionCreate


from questions.use_cases.get_daily_question import get_daily_question


from questions.infrastructure.repositories.question_repository import QuestionRepository
from questions.use_cases.list_questions import ListQuestionsUseCase

router = APIRouter(
    prefix="/question",
    tags=["Questions"]
)


@router.get("/daily/")
def _daily_question():
    return get_daily_question()


from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session

from questions.presentation.schemas.question import QuestionCreate, QuestionResponse
from questions.infrastructure.repositories.question_repository import QuestionRepository
from questions.use_cases.create_question import CreateQuestionUseCase


router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


@router.post(
    "/create/",
    response_model=QuestionResponse
)
async def create_question(
    question: QuestionCreate,
    session: AsyncSession = Depends(get_session)
):
    repository = QuestionRepository(session)

    use_case = CreateQuestionUseCase(repository)

    created_question = await use_case.execute(question)

    return created_question


@router.get(
    "/list",
    response_model=list[QuestionResponse]
)
async def list_questions(
    session: AsyncSession = Depends(get_session),
):
    repository =  QuestionRepository(session)
    use_case = ListQuestionsUseCase(repository)
    return await use_case.execute()

