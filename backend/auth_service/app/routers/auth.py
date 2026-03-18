import secrets

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError

from app.config import settings
from app.db import password_reset_tokens_collection, users_collection
from app.dependencies import get_current_user, get_current_verified_user
from app.rate_limit import limit_requests
from app.schemas.auth import (
    ChangePasswordRequest,
    Enable2FAResponse,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RecoveryCodesResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegenerateRecoveryCodesRequest,
    RegisterRequest,
    ResendVerificationRequest,
    UpdateProfileRequest,
    VerifyEmailRequest,
    Verify2FARequest,
)
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
)
from app.services.password_reset_service import (
    consume_password_reset_token,
    create_password_reset_token,
)
from app.services.password_service import hash_password, verify_password
from app.services.session_service import (
    clear_auth_cookies,
    get_refresh_token_from_request,
    get_refresh_session,
    persist_refresh_session,
    revoke_all_sessions_for_user,
    revoke_session,
    set_auth_cookies,
)
from app.services.token_service import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.twofa_service import (
    generate_2fa_secret,
    generate_recovery_codes,
    get_totp_uri,
    hash_recovery_code,
    verify_2fa_code,
    verify_recovery_code,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _public_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "is_verified": user.get("is_verified", False),
        "two_factor_enabled": user.get("two_factor_enabled", False),
    }


async def _issue_session(user: dict, request: Request, response: Response) -> dict:
    access_token = create_access_token(str(user["_id"]))
    refresh_token = create_refresh_token(str(user["_id"]))
    await persist_refresh_session(user["_id"], refresh_token, request)
    set_auth_cookies(response, access_token, refresh_token)
    return {
        "token_type": "session",
        "access_expires_in": settings.access_token_expire_minutes * 60,
        "refresh_expires_in": settings.refresh_token_expire_days * 24 * 60 * 60,
        "user": _public_user(user),
    }


async def _verify_second_factor(user: dict, data: LoginRequest) -> None:
    if not user.get("two_factor_enabled"):
        return

    recovery_code = (data.recovery_code or "").strip()
    if recovery_code:
        valid, remaining_codes = verify_recovery_code(
            user.get("two_factor_recovery_codes"),
            recovery_code,
        )
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid recovery code")

        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"two_factor_recovery_codes": remaining_codes}},
        )
        return

    if not data.twofa_code:
        raise HTTPException(status_code=403, detail="2FA code required")

    if not verify_2fa_code(user["two_factor_secret"], data.twofa_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")


@router.post("/register")
async def register(
    data: RegisterRequest,
    _: None = Depends(
        limit_requests(
            "register",
            settings.register_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
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
        "two_factor_recovery_codes": [],
    }

    result = await users_collection.insert_one(user_doc)
    send_verification_email(data.email, verification_token)

    return {
        "message": "User created. Check your email for the verification link.",
        "user_id": str(result.inserted_id),
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    _: None = Depends(
        limit_requests(
            "login",
            settings.login_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
    user = await users_collection.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email verification required")

    await _verify_second_factor(user, data)
    return await _issue_session(user, request, response)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    data: RefreshTokenRequest | None = None,
    _: None = Depends(
        limit_requests(
            "refresh",
            settings.refresh_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
    raw_refresh_token = get_refresh_token_from_request(
        request,
        data.refresh_token if data else None,
    )
    if not raw_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    try:
        session, payload = await get_refresh_session(raw_refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email verification required")

    await revoke_session(session["jti"])
    return await _issue_session(user, request, response)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    data: RefreshTokenRequest | None = None,
    _: None = Depends(
        limit_requests(
            "logout",
            settings.logout_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
    raw_refresh_token = get_refresh_token_from_request(
        request,
        data.refresh_token if data else None,
    )
    if raw_refresh_token:
        try:
            payload = decode_token(raw_refresh_token, expected_type=REFRESH_TOKEN_TYPE)
            if payload.get("jti"):
                await revoke_session(payload["jti"])
        except JWTError:
            pass

    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    response: Response,
    current_user=Depends(get_current_user),
):
    await revoke_all_sessions_for_user(current_user["_id"])
    clear_auth_cookies(response)
    return {"message": "Logged out from all devices"}


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return _public_user(current_user)


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


@router.patch("/password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    response: Response,
    current_user=Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password_hash": hash_password(data.new_password)}},
    )
    await revoke_all_sessions_for_user(current_user["_id"])
    clear_auth_cookies(response)
    return {"message": "Password updated successfully. Please sign in again."}


@router.post("/verify-email", response_model=MessageResponse)
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


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    _: None = Depends(
        limit_requests(
            "resend-verification",
            settings.password_reset_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        return {"message": "If that email exists, a verification email has been sent."}

    if user.get("is_verified"):
        return {"message": "If that email exists, a verification email has been sent."}

    token = secrets.token_urlsafe(32)
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"verification_token": token}},
    )
    send_verification_email(user["email"], token)
    return {"message": "If that email exists, a verification email has been sent."}


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    _: None = Depends(
        limit_requests(
            "password-reset",
            settings.password_reset_rate_limit_requests,
            settings.auth_rate_limit_window_seconds,
        )
    ),
):
    user = await users_collection.find_one({"email": data.email})
    if user:
        token = await create_password_reset_token(user["_id"])
        send_password_reset_email(user["email"], token)

    return {
        "message": "If that email exists, a password reset link has been sent."
    }


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(data: PasswordResetConfirmRequest):
    user_id = await consume_password_reset_token(data.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"password_hash": hash_password(data.new_password)}},
    )
    await revoke_all_sessions_for_user(user_id)
    await password_reset_tokens_collection.delete_many({"user_id": user_id})
    return {"message": "Password reset successfully"}


@router.post("/2fa/setup", response_model=Enable2FAResponse)
async def setup_2fa(current_user=Depends(get_current_verified_user)):
    secret = generate_2fa_secret()
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"two_factor_secret": secret}},
    )
    return {
        "secret": secret,
        "otp_auth_url": get_totp_uri(current_user["email"], secret),
    }


@router.post("/2fa/enable", response_model=RecoveryCodesResponse)
async def enable_2fa(
    data: Verify2FARequest,
    current_user=Depends(get_current_verified_user),
):
    secret = current_user.get("two_factor_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA setup not started")

    if not verify_2fa_code(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")

    recovery_codes = generate_recovery_codes()
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "two_factor_enabled": True,
                "two_factor_recovery_codes": [
                    hash_recovery_code(code) for code in recovery_codes
                ],
            }
        },
    )

    return {
        "message": "2FA enabled successfully",
        "recovery_codes": recovery_codes,
    }


@router.post("/2fa/recovery-codes/regenerate", response_model=RecoveryCodesResponse)
async def regenerate_recovery_codes(
    data: RegenerateRecoveryCodesRequest,
    current_user=Depends(get_current_verified_user),
):
    if not verify_password(data.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if not current_user.get("two_factor_enabled"):
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    recovery_codes = generate_recovery_codes()
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$set": {
                "two_factor_recovery_codes": [
                    hash_recovery_code(code) for code in recovery_codes
                ]
            }
        },
    )
    return {
        "message": "Recovery codes regenerated successfully",
        "recovery_codes": recovery_codes,
    }
