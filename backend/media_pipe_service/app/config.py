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

    # S3D classifier settings (ai-forever/easy_sign — RSL word recognition)
    USE_S3D: bool = True
    S3D_MODEL_PATH: str = ""  # Empty → auto-download from GitHub
    S3D_CLASS_LIST_PATH: str = ""  # Empty → auto-download from GitHub
    S3D_WINDOW_SIZE: int = 32  # Frames per inference window
    S3D_THRESHOLD: float = 0.5  # Minimum confidence to emit a prediction

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
