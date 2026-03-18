from pydantic import BaseModel, EmailStr
from typing import Optional


class UserInDB(BaseModel):
    email: EmailStr
    name: str
    password_hash: str
    is_verified: bool = False
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None