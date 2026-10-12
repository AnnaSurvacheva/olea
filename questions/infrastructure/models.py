from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


from core.database import Base


class QuestionModel(Base):
    """
    Database model representing a question.

    This model is mapped to the "questions" table
    in PostgreSQL.
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)

    question: Mapped[str] = mapped_column(String(300), nullable=False)

    

