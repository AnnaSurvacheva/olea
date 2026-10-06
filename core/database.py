from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "postgresql+asyncpg://anna@localhost:5432/reflection_db"


engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True: SQL в консоль, потом можно убрать


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in the project."""
    pass


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session