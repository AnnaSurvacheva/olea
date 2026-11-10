"""Turn domain errors of the users module into HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from users.domain.exceptions import (
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

   