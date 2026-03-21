"""Configuration settings for MediaPipe service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Service settings
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # MediaPipe settings
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_NUM_HANDS: int = 1
    MIN_DETECTION_CONFIDENCE: float = 0.5
    MIN_TRACKING_CONFIDENCE: float = 0.5
    
    # LLM Service
    LLM_SERVICE_URL: str = "http://localhost:8002"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost"

    # Sign buffer settings
    SIGN_BUFFER_TIMEOUT_MS: int = 1500  # Time before committing sign sequence
    MIN_SEQUENCE_LENGTH: int = 2

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
