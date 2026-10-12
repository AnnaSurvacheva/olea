"""Conversion between the ORM model and the domain entity."""

from users.domain.entities.user import User
from users.infrastructure.models import UsersModel


def to_entity(model: UsersModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        display_name=model.display_name,
        timezone=model.timezone,
        created_at=model.created_at,
    )
