import hashlib
import secrets

import pyotp

from app.config import settings


def generate_2fa_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(email: str, secret: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="VUR Translator")


def verify_2fa_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_recovery_codes() -> list[str]:
    return [
        f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        for _ in range(settings.recovery_codes_count)
    ]


def hash_recovery_code(code: str) -> str:
    normalized = code.replace("-", "").strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def verify_recovery_code(hashed_codes: list[str] | None, code: str) -> tuple[bool, list[str]]:
    if not hashed_codes:
        return False, []

    target = hash_recovery_code(code)
    remaining = [value for value in hashed_codes if value != target]
    return len(remaining) != len(hashed_codes), remaining
