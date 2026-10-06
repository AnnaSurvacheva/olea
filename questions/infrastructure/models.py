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

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    
    question: Mapped[str] = mapped_column(
        String(300),
        nullable=False
    )

class UsersModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False # TODO:при добавлении аунтификациии через apple - почту сделать не обязательной 
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
          nullable=True
        )
    apple_sub: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
        )
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False
        )
