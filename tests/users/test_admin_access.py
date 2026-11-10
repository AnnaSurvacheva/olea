import pytest
from fastapi import HTTPException

from tests.users.factories import make_user
from users.presentation.dependencies import get_current_admin


async def test_admin_dependency_accepts_admin_user() -> None:
    admin = make_user(role="admin")

    assert await get_current_admin(admin) == admin


async def test_admin_dependency_rejects_regular_user() -> None:
    with pytest.raises(HTTPException) as error:
        await get_current_admin(make_user())

    assert error.value.status_code == 403
