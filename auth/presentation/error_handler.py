"""Turn domain errors of the auth module into HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth.domain.exceptions import (
    EmailAlreadyRegistered,
    WeakPassword,
)


def register_auth_error(app: FastAPI) -> None:
    """Teach the application how to answer when a auth error is raised."""
    @app.exception_handler(EmailAlreadyRegistered)
    async def email_already_registered(
        request: Request, 
        error: EmailAlreadyRegistered
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})
    
    @app.exception_handler(WeakPassword)
    async def weak_password(
        request: Request,
        error: WeakPassword,
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})
    

