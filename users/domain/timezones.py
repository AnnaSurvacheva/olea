"""Timezone validation rules."""

from zoneinfo import available_timezones

from users.domain.exceptions import InvalidTimezone

KNOWN_TIMEZONES = available_timezones()


def validate_timezone(value: str) -> None:
    """Raise InvalidTimezone if the value is not an IANA timezone name."""
    if value not in KNOWN_TIMEZONES:
        raise InvalidTimezone(value)
