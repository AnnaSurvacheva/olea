"""Unit tests for the GetProfile use case."""

import pytest

from tests.users.factories import make_user
from tests.users.fakes import InMemoryUserRepository
from users.domain.exceptions import UserNotFound
from users.use_cases.get_profile import GetProfile


async def test_return_profile_when_user_exist()-> None:
    user = make_user()
    repository = InMemoryUserRepository([user])
    use_cases = GetProfile(repository)
    result = await use_cases.execute(1)
    assert result == user


async def test_raises_user_not_found_when_user_is_missing()-> None:
    repository = InMemoryUserRepository(None)
    use_cases = GetProfile(repository)
    with pytest.raises(UserNotFound) as error:
        await use_cases.execute(99)
    assert error.value.user_id == 99





