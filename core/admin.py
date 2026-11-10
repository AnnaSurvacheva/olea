import hmac
from hashlib import sha256
from typing import Any, ClassVar

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import Response

from auth.domain.email import normalize_email
from auth.infrastructure.password_hasher import Argon2PasswordHasher
from core.database import AsyncSessionLocal, engine
from core.settings import get_settings
from questions.infrastructure.models import QuestionModel
from users.infrastructure.repositories.user_repository import SqlAlchemyUserRepository


class QuestionAdmin(ModelView, model=QuestionModel):
    column_list: ClassVar[list[Any]] = [
        QuestionModel.id,
        QuestionModel.question,
        QuestionModel.for_day,
    ]
    form_columns: ClassVar[list[Any]] = [
        QuestionModel.question,
        QuestionModel.for_day,
    ]

    async def on_model_change(
        self,
        data: dict[str, Any],
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        async with AsyncSessionLocal() as session:
            existing_question = await session.scalar(
                select(QuestionModel.id).where(
                    QuestionModel.for_day == data["for_day"],
                    QuestionModel.id != getattr(model, "id", None),
                )
            )
        if existing_question is not None:
            raise ValueError(
                f"A question is already scheduled for {data['for_day'].isoformat()}"
            )


class AdminAuthentication(AuthenticationBackend):
    def __init__(self) -> None:
        secret = get_settings().jwt_secret_key.get_secret_value().encode()
        session_secret = hmac.new(secret, b"sqladmin-session", sha256).hexdigest()
        super().__init__(secret_key=session_secret)

    async def login(self, request: Request) -> Response | bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        if not isinstance(email, str) or not isinstance(password, str):
            return False

        settings = get_settings()
        hasher = Argon2PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost,
            parallelism=settings.argon2_parallelism,
        )
        async with AsyncSessionLocal() as session:
            repository = SqlAlchemyUserRepository(session)
            credentials = await repository.get_credentials_by_email(
                normalize_email(email)
            )
            if (
                credentials is None
                or credentials.user.role != "admin"
                or credentials.hashed_password is None
            ):
                await hasher.verify_in_thread(password, settings.dummy_password_hash)
                return False
            if not await hasher.verify_in_thread(
                password,
                credentials.hashed_password,
            ):
                return False

        request.session.clear()
        request.session["user_id"] = credentials.user.id
        return True

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        user_id = request.session.get("user_id")
        if not isinstance(user_id, int):
            return False

        async with AsyncSessionLocal() as session:
            user = await SqlAlchemyUserRepository(session).get(user_id)
        return user is not None and user.role == "admin"


def setup_admin(app: FastAPI) -> None:
    admin = Admin(app, engine, authentication_backend=AdminAuthentication())
    admin.add_view(QuestionAdmin)
