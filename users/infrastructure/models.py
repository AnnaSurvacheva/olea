from datetime import datetime

from sqlalchemy import DateTime, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UsersModel(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("ix_users_email_lower", func.lower(text("email")), unique=True),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,  # TODO: при добавлении аутентификации через apple - почту сделать не обязательной
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    apple_sub: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default="UTC",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
