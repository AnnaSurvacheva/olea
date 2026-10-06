from fastapi import FastAPI
from sqladmin import Admin, ModelView

from core.database import engine
from questions.infrastructure.models import QuestionModel


class QuestionAdmin(ModelView, model=QuestionModel):
    column_list = [QuestionModel.id, QuestionModel.question]
    form_columns = [QuestionModel.question]

def setup_admin(app: FastAPI) -> None:
    admin = Admin(app, engine)
    admin.add_view(QuestionAdmin)