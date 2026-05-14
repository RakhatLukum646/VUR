from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from bson import ObjectId

from app.config import settings
from app.db import users_collection
from app.services.token_service import ACCESS_TOKEN_TYPE, decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    token = None
    if credentials is not None:
        token = credentials.credentials
    else:
        token = request.cookies.get(settings.access_cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

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


async def get_current_admin_user(
    current_user=Depends(get_current_verified_user),
):
    role = (current_user.get("role") or "").lower()
    email = (current_user.get("email") or "").lower()
    if role == "admin" or email in settings.admin_email_list:
        return current_user
    raise HTTPException(status_code=403, detail="Admin access required")
