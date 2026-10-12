"""Turn domain errors of the users module into HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from users.domain.exceptions import (
    EmailAlreadyTaken,
    InvalidCredentials,
    InvalidTimezone,
    UserNotFound,
)


def register_user_error_handlers(app: FastAPI) -> None:
    """Teach the application how to answer when a users error is raised."""

    @app.exception_handler(UserNotFound)
    async def handle_user_not_found(
        request: Request, error: UserNotFound
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(InvalidTimezone)
    async def handle_invalid_timezone(
        request: Request, error: InvalidTimezone
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "type": "invalid_timezone",
                        "loc": ["body", "timezone"],
                        "msg": str(error),
                        "input": error.value,
                    }
                ]
            },
        )

    @app.exception_handler(EmailAlreadyTaken)
    async def handle_email_already_taken(
        request: Request, error: EmailAlreadyTaken
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(InvalidCredentials)
    async def handle_invalid_credentials(
        request: Request, error: InvalidCredentials
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(error)})
