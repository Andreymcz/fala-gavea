from __future__ import annotations

from datetime import datetime, timedelta, UTC

import jwt

from fala_gavea import config
from fala_gavea.domain.exceptions import InvalidCredentialsError


class JWTService:
    def __init__(self) -> None:
        if not config.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is not set")
        self._secret = config.JWT_SECRET_KEY
        self._algorithm = config.JWT_ALGORITHM

    def create_access_token(self, user_id: str, role: str, expires_delta: timedelta) -> str:
        payload = {
            "sub": user_id,
            "role": role,
            "exp": datetime.now(UTC) + expires_delta,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            raise InvalidCredentialsError("Token expired")
        except jwt.InvalidTokenError:
            raise InvalidCredentialsError("Invalid token")
