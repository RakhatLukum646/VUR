from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from bson import ObjectId

from app.db import users_collection
from app.services.token_service import ACCESS_TOKEN_TYPE, decode_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_verified_user(
    current_user=Depends(get_current_user),
):
    if not current_user.get("is_verified", False):
        raise HTTPException(
            status_code=403,
            detail="Email verification required",
        )

    return current_user
