from pymongo import ASCENDING, AsyncMongoClient
from app.config import settings

client = AsyncMongoClient(settings.mongodb_url)

db = client[settings.mongodb_db]

users_collection = db["users"]
auth_sessions_collection = db["auth_sessions"]
password_reset_tokens_collection = db["password_reset_tokens"]


async def ensure_indexes() -> None:
    await users_collection.create_index([("email", ASCENDING)], unique=True)
    await auth_sessions_collection.create_index([("jti", ASCENDING)], unique=True)
    await auth_sessions_collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
    await auth_sessions_collection.create_index([("user_id", ASCENDING), ("revoked_at", ASCENDING)])
    await password_reset_tokens_collection.create_index([("token_hash", ASCENDING)], unique=True)
    await password_reset_tokens_collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
