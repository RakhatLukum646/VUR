from datetime import datetime, timedelta, UTC
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt

from app.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _build_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return _build_token(
        user_id=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return _build_token(
        user_id=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise JWTError("Unexpected token type")

    return payload
