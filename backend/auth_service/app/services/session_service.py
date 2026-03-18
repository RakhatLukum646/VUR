from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import Request, Response
from jose import JWTError

from app.config import settings
from app.db import auth_sessions_collection
from app.services.token_service import REFRESH_TOKEN_TYPE, decode_token


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "path": "/",
    }
    if settings.cookie_domain:
        cookie_kwargs["domain"] = settings.cookie_domain

    response.set_cookie(
        settings.access_cookie_name,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **cookie_kwargs,
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: Response) -> None:
    cookie_kwargs = {"path": "/"}
    if settings.cookie_domain:
        cookie_kwargs["domain"] = settings.cookie_domain

    response.delete_cookie(settings.access_cookie_name, **cookie_kwargs)
    response.delete_cookie(settings.refresh_cookie_name, **cookie_kwargs)


def get_refresh_token_from_request(request: Request, body_token: str | None = None) -> str | None:
    return body_token or request.cookies.get(settings.refresh_cookie_name)


def _request_metadata(request: Request) -> dict:
    client_host = request.client.host if request.client else None
    return {
        "ip_address": client_host,
        "user_agent": request.headers.get("user-agent"),
    }


async def persist_refresh_session(user_id: ObjectId, refresh_token: str, request: Request) -> dict:
    payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    exp = payload.get("exp")
    jti = payload.get("jti")

    if not exp or not jti:
        raise JWTError("Invalid refresh token payload")

    session = {
        "user_id": user_id,
        "jti": jti,
        "token_hash": hash_secret(refresh_token),
        "created_at": datetime.now(UTC),
        "last_used_at": datetime.now(UTC),
        "expires_at": datetime.fromtimestamp(exp, tz=UTC),
        "revoked_at": None,
        **_request_metadata(request),
    }
    await auth_sessions_collection.insert_one(session)
    return session


async def get_refresh_session(refresh_token: str) -> tuple[dict, dict]:
    payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not user_id or not ObjectId.is_valid(user_id) or not jti:
        raise JWTError("Invalid refresh token payload")

    session = await auth_sessions_collection.find_one({"jti": jti})
    if not session:
        raise JWTError("Refresh session not found")

    if session.get("revoked_at") is not None:
        raise JWTError("Refresh session revoked")

    if session.get("token_hash") != hash_secret(refresh_token):
        await revoke_session(session["jti"])
        raise JWTError("Refresh token mismatch")

    if session.get("expires_at") and session["expires_at"] <= datetime.now(UTC):
        raise JWTError("Refresh session expired")

    return session, payload


async def revoke_session(jti: str) -> None:
    await auth_sessions_collection.update_one(
        {"jti": jti, "revoked_at": None},
        {"$set": {"revoked_at": datetime.now(UTC)}},
    )


async def revoke_all_sessions_for_user(user_id: ObjectId) -> None:
    await auth_sessions_collection.update_many(
        {"user_id": user_id, "revoked_at": None},
        {"$set": {"revoked_at": datetime.now(UTC)}},
    )
