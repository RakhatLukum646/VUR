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

class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class VerifyEmailRequest(BaseModel):
    token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Enable2FAResponse(BaseModel):
    secret: str
    otp_auth_url: str


class Verify2FARequest(BaseModel):
    code: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    refresh_expires_in: int
    user: dict


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    refresh_expires_in: int
    user: dict
