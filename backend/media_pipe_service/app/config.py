"""Configuration settings for MediaPipe service."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service settings
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # MediaPipe settings
    CONFIDENCE_THRESHOLD: float = 0.7
    MAX_NUM_HANDS: int = 1
    MIN_DETECTION_CONFIDENCE: float = 0.5
    MIN_TRACKING_CONFIDENCE: float = 0.5
    
    # LLM Service
    LLM_SERVICE_URL: str = "http://localhost:8002"
    
    # Sign buffer settings
    SIGN_BUFFER_TIMEOUT_MS: int = 2000  # Time before committing sign sequence
    MIN_SEQUENCE_LENGTH: int = 2
    
    class Config:
        env_file = ".env"


settings = Settings()
