from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.settings import DatabaseSettings

DATABASE_URL = DatabaseSettings().database_url

engine = create_async_engine(
    DATABASE_URL,
    hide_parameters=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in the project."""



async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
