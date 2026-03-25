"""Pytest configuration for media_pipe_service tests."""
import os
import sys
from pathlib import Path

import pytest

# Ensure the service root is on the path for all tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Default env vars required by config/ws_auth modules.
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("CONFIDENCE_THRESHOLD", "0.7")
os.environ.setdefault("LLM_SERVICE_URL", "http://llm-service:8002")
os.environ.setdefault("PORT", "8001")
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests that require network access or heavy computation "
        "(skip with: pytest -m 'not slow')",
    )
