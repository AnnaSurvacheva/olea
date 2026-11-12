"""Structured security logging for authentication events."""

import logging


class LoggingSecurityEventLogger:
    """Write authentication security events through Python's logging system."""

    def __init__(self) -> None:
        """Select the dedicated authentication security logger."""
        self._logger = logging.getLogger("security.auth")

    def log_refresh_token_reuse(
        self,
        family_id: str,
        user_id: int,
        occurred_at: str,
    ) -> None:
        """Log token-family reuse details without including any token value."""
        event_type = "refresh_token_reuse_detected"
        self._logger.warning(
            "security_event=%s family_id=%s user_id=%s occurred_at=%s",
            event_type,
            family_id,
            user_id,
            occurred_at,
            extra={
                "security_event_type": event_type,
                "family_id": family_id,
                "user_id": user_id,
                "occurred_at": occurred_at,
            },
        )
