from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
    )


# Схема для чтения вопроса (ответ сервера)
class QuestionResponse(BaseModel):
    id: int
    question: str

    model_config = ConfigDict(from_attributes=True)
