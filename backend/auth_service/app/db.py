from pymongo import AsyncMongoClient
from app.config import settings

client = AsyncMongoClient(settings.mongodb_url)

db = client[settings.mongodb_db]

users_collection = db["users"]