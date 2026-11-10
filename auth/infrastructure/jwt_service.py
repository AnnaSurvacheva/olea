from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from auth.domain.exceptions import InvalidToken
from core.settings import Settings

JWT_ALGORITHM = "HS256"


class JwtTokenService:
    """Issues signed access tokens using JWT."""

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key.get_secret_value()
        self._issuer = settings.jwt_issuer
        self._ttl_minutes = settings.access_token_ttl_minutes

    def issue_access(self, user_id: int) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._ttl_minutes)

        claims = {
            "sub": str(user_id),
            "iss": self._issuer,
            "iat": now,
            "exp": expires_at,
            "jti": str(uuid4()),
            "typ": "access",
        }

        return jwt.encode(
            claims,
            self._secret_key,
            algorithm=JWT_ALGORITHM,
        )

    def decode_access(self, token: str) -> int:
        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=[JWT_ALGORITHM],
                issuer=self._issuer,
                options={"require": ["exp", "iss", "sub", "jti"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken() from exc

        if claims.get("typ") != "access":
            raise InvalidToken()

        try:
            return int(claims["sub"])
        except (TypeError, ValueError) as exc:
            raise InvalidToken() from exc
