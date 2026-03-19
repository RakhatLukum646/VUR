"""Minimal JWT verification for WebSocket connections."""
import os

from jose import JWTError, jwt

_ACCESS_TYPE = "access"


def verify_ws_token(token: str) -> dict:
    """Decode and validate an access JWT. Raises JWTError on any failure.

    The secret and algorithm are read from the environment at call time so
    that test suites can set JWT_SECRET before the first request without
    being defeated by module-level caching.
    """
    secret = os.environ.get("JWT_SECRET", "change-me-in-production")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError:
        raise JWTError("Invalid token")
    if payload.get("type") != _ACCESS_TYPE:
        raise JWTError("Wrong token type")
    return payload
