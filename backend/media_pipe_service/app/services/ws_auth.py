"""Minimal JWT verification for WebSocket connections."""
import os

from jose import JWTError, jwt

_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_ACCESS_TYPE = "access"


def verify_ws_token(token: str) -> dict:
    """Decode and validate an access JWT. Raises JWTError on any failure."""
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        raise JWTError("Invalid token")
    if payload.get("type") != _ACCESS_TYPE:
        raise JWTError("Wrong token type")
    return payload
