from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from bson import ObjectId

from app.config import settings
from app.db import password_reset_tokens_collection
from app.services.session_service import hash_secret


async def create_password_reset_token(user_id: ObjectId) -> str:
    raw_token = secrets.token_urlsafe(32)
    await password_reset_tokens_collection.insert_one(
        {
            "user_id": user_id,
            "token_hash": hash_secret(raw_token),
            "created_at": datetime.now(UTC),
            "expires_at": datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_expire_minutes),
            "used_at": None,
        }
    )
    return raw_token


async def consume_password_reset_token(raw_token: str) -> ObjectId | None:
    token_hash = hash_secret(raw_token)
    record = await password_reset_tokens_collection.find_one(
        {"token_hash": token_hash, "used_at": None}
    )
    if not record:
        return None

    if record["expires_at"] <= datetime.now(UTC):
        return None

    await password_reset_tokens_collection.update_one(
        {"_id": record["_id"]},
        {"$set": {"used_at": datetime.now(UTC)}},
    )
    return record["user_id"]
