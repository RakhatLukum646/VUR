from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str

    jwt_secret: str
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
