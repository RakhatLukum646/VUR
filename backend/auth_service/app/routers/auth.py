import secrets
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.db import users_collection
from app.dependencies import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
    VerifyEmailRequest,
    Enable2FAResponse,
    Verify2FARequest,
)
from app.services.password_service import hash_password, verify_password
from app.services.token_service import create_access_token
from app.services.email_service import send_verification_email
from app.services.twofa_service import (
    generate_2fa_secret,
    get_totp_uri,
    verify_2fa_code,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterRequest):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    verification_token = secrets.token_urlsafe(32)

    user_doc = {
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "is_verified": False,
        "verification_token": verification_token,
        "two_factor_enabled": False,
        "two_factor_secret": None,
    }

    result = await users_collection.insert_one(user_doc)

    send_verification_email(data.email, verification_token)

    return {
        "message": "User created. Check terminal for verification link.",
        "user_id": str(result.inserted_id),
    }


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):

    user = await users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2FA check
    if user.get("two_factor_enabled"):

        if not data.twofa_code:
            raise HTTPException(
                status_code=403,
                detail="2FA code required"
            )

        if not verify_2fa_code(user["two_factor_secret"], data.twofa_code):
            raise HTTPException(
                status_code=401,
                detail="Invalid 2FA code"
            )

    token = create_access_token(str(user["_id"]))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "is_verified": user.get("is_verified"),
            "two_factor_enabled": user.get("two_factor_enabled"),
        }
    }


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "name": current_user["name"],
        "email": current_user["email"],
        "is_verified": current_user.get("is_verified", False),
        "two_factor_enabled": current_user.get("two_factor_enabled", False),
    }


@router.patch("/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user=Depends(get_current_user),
):
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"name": data.name}},
    )

    return {"message": "Name updated successfully"}


@router.patch("/password")
async def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(data.new_password)}},
    )

    return {"message": "Password updated successfully"}


@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest):
    user = await users_collection.find_one({"verification_token": data.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"is_verified": True},
            "$unset": {"verification_token": ""},
        },
    )

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(current_user=Depends(get_current_user)):
    if current_user.get("is_verified"):
        return {"message": "Email already verified"}

    token = secrets.token_urlsafe(32)

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"verification_token": token}},
    )

    send_verification_email(current_user["email"], token)
    return {"message": "Verification email sent"}


@router.post("/2fa/setup", response_model=Enable2FAResponse)
async def setup_2fa(current_user=Depends(get_current_user)):
    secret = generate_2fa_secret()

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"two_factor_secret": secret}},
    )

    otp_auth_url = get_totp_uri(current_user["email"], secret)

    return {
        "secret": secret,
        "otp_auth_url": otp_auth_url,
    }


@router.post("/2fa/enable")
async def enable_2fa(
    data: Verify2FARequest,
    current_user=Depends(get_current_user),
):
    secret = current_user.get("two_factor_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA setup not started")

    if not verify_2fa_code(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"two_factor_enabled": True}},
    )

    return {"message": "2FA enabled successfully"}