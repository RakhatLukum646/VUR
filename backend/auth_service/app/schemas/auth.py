from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    twofa_code: Optional[str] = None
    recovery_code: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class Enable2FAResponse(BaseModel):
    secret: str
    otp_auth_url: str


class Verify2FARequest(BaseModel):
    code: str


class RecoveryCodesResponse(BaseModel):
    message: str
    recovery_codes: list[str]


class RegenerateRecoveryCodesRequest(BaseModel):
    current_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class LoginResponse(BaseModel):
    token_type: str = "session"
    access_expires_in: int
    refresh_expires_in: int
    user: dict


class RefreshTokenResponse(BaseModel):
    token_type: str = "session"
    access_expires_in: int
    refresh_expires_in: int
    user: dict


class MessageResponse(BaseModel):
    message: str
