from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BANNED_SECRETS = {"change-me-in-production", "changeme", "secret", ""}


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str

    jwt_secret: str

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        if v.lower() in _BANNED_SECRETS:
            raise ValueError(
                "jwt_secret is set to a known insecure default. "
                "Generate a strong secret: openssl rand -hex 32"
            )
        if len(v) < 32:
            raise ValueError(
                "jwt_secret must be at least 32 characters long."
            )
        return v
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_expire_minutes: int = 30
    recovery_codes_count: int = 8

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost"
    access_cookie_name: str = "vur_access_token"
    refresh_cookie_name: str = "vur_refresh_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    log_level: str = "INFO"

    auth_rate_limit_window_seconds: int = 60
    login_rate_limit_requests: int = 10
    register_rate_limit_requests: int = 5
    register_rate_limit_window_seconds: int = 3600  # 5 registrations per hour
    refresh_rate_limit_requests: int = 20
    password_reset_rate_limit_requests: int = 5
    logout_rate_limit_requests: int = 20

    email_host: str
    email_port: int
    email_user: str
    email_password: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
