from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=300,
    )
    for_day: date


class QuestionResponse(BaseModel):
    id: int
    question: str
    for_day: date

    model_config = ConfigDict(from_attributes=True)
