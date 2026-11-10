"""Helpers that build test data."""

from datetime import UTC, datetime

from users.domain.entities.user import User


def make_user(user_id: int = 1, role: str = "user") -> User:
    return User(
        id=user_id,
        email="anna@example.com",
        display_name="Anna",
        timezone="Europe/Moscow",
        created_at=datetime(2026, 10, 8, tzinfo=UTC),
        role=role,
    )
