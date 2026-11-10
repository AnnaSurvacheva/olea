from typing import Annotated

from fastapi import APIRouter, Depends, status

from auth.presentation.dependencies import get_login_user, get_register_user
from auth.presentation.schemas.login_request import LoginRequest
from auth.presentation.schemas.register import RegisterRequest, RegisterResponse
from auth.presentation.schemas.token_response import TokenResponse
from auth.use_cases.login_user import LoginUser
from auth.use_cases.register_user import RegisterUser

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user)],
) -> RegisterResponse:
    user = await use_case.execute(
        email=body.email,
        password=body.password,
        timezone=body.timezone,
    )
    return RegisterResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    use_case: Annotated[LoginUser, Depends(get_login_user)],
) -> TokenResponse:
    result = await use_case.execute(
        email=body.email,
        password=body.password,
    )
    return TokenResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
    )
