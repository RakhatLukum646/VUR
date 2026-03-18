from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    frontend_url: str = "http://localhost:5173"

    email_host: str
    email_port: int
    email_user: str
    email_password: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()