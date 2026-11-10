from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class QuestionModel(Base):
    """
    Database model representing a question.

    This model is mapped to the "questions" table
    in PostgreSQL.
    """

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("for_day", name="uq_questions_for_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    question: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    for_day: Mapped[date] = mapped_column(Date, nullable=False)
