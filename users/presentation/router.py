"""HTTP endpoints for the current user's profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from users.presentation.dependencies import (
    get_current_user_id,
    get_delete_account,
    get_get_profile,
    get_update_profile,
)
from users.presentation.schemas.user import UpdateProfileRequest, UserProfileResponse
from users.use_cases.delete_account import DeleteAccount
from users.use_cases.get_profile import GetProfile
from users.use_cases.update_profile import UpdateProfile

router = APIRouter(prefix="/users", tags=["Users"])

CurrentUserId = Annotated[int, Depends(get_current_user_id)]


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    user_id: CurrentUserId,
    use_case: Annotated[GetProfile, Depends(get_get_profile)],
) -> UserProfileResponse:
    user = await use_case.execute(user_id)
    return UserProfileResponse.model_validate(user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    body: UpdateProfileRequest,
    user_id: CurrentUserId,
    use_case: Annotated[UpdateProfile, Depends(get_update_profile)],
) -> UserProfileResponse:
    changes = body.model_dump(exclude_unset=True)
    user = await use_case.execute(user_id, changes)  # type: ignore[arg-type]
    return UserProfileResponse.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user_id: CurrentUserId,
    use_case: Annotated[DeleteAccount, Depends(get_delete_account)],
) -> None:
    await use_case.execute(user_id)