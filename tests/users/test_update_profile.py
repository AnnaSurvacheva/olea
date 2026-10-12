"""Unit tests for the UpdateProfile use case."""

import pytest

from tests.users.factories import make_user
from tests.users.fakes import InMemoryUserRepository
from users.domain.exceptions import InvalidTimezone, UserNotFound
from users.use_cases.update_profile import UpdateProfile


async def test_updates_timezone_when_zone_is_valid() -> None:
    repository = InMemoryUserRepository([make_user()])
    use_case = UpdateProfile(repository)

    result = await use_case.execute(1, {"timezone": "Asia/Tokyo"})

    assert result.timezone == "Asia/Tokyo"
    assert result.display_name == "Anna"


async def test_rejects_unknown_timezone() -> None:
    repository = InMemoryUserRepository([make_user()])
    use_case = UpdateProfile(repository)

    with pytest.raises(InvalidTimezone) as error:
        await use_case.execute(1, {"timezone": "Mars/Phobos"})

    assert error.value.value == "Mars/Phobos"
    assert repository.users[1].timezone == "Europe/Moscow"


async def test_empty_request_changes_nothing() -> None:
    user = make_user()
    use_case = UpdateProfile(InMemoryUserRepository([user]))

    result = await use_case.execute(1, {})

    assert result == user


async def test_raises_user_not_found_when_user_is_missing() -> None:
    use_case = UpdateProfile(InMemoryUserRepository())

    with pytest.raises(UserNotFound):
        await use_case.execute(99, {"display_name": "Anna"})

