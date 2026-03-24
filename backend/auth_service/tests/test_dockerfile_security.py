"""
Verify that all service Dockerfiles run as a non-root user.
These are static-analysis tests — no Docker daemon required.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]  # /home/rakhat/VUR


def _read_dockerfile(relative_path: str) -> str:
    return (BASE_DIR / relative_path / "Dockerfile").read_text()


def test_auth_service_dockerfile_has_non_root_user():
    content = _read_dockerfile("backend/auth_service")
    assert "USER appuser" in content, (
        "auth_service Dockerfile must contain 'USER appuser' to run as non-root"
    )


def test_llm_service_dockerfile_has_non_root_user():
    content = _read_dockerfile("backend/llm_service")
    assert "USER appuser" in content, (
        "llm_service Dockerfile must contain 'USER appuser' to run as non-root"
    )


def test_media_pipe_service_dockerfile_has_non_root_user():
    content = _read_dockerfile("backend/media_pipe_service")
    assert "USER appuser" in content, (
        "media_pipe_service Dockerfile must contain 'USER appuser' to run as non-root"
    )


def test_frontend_dockerfile_has_non_root_user():
    content = _read_dockerfile("frontend")
    assert "USER nginx" in content, (
        "frontend Dockerfile must contain 'USER nginx' to run as non-root"
    )


def test_auth_service_dockerfile_creates_appuser():
    content = _read_dockerfile("backend/auth_service")
    assert "adduser" in content or "useradd" in content, (
        "auth_service Dockerfile must create the appuser"
    )


def test_llm_service_dockerfile_creates_appuser():
    content = _read_dockerfile("backend/llm_service")
    assert "adduser" in content or "useradd" in content, (
        "llm_service Dockerfile must create the appuser"
    )


def test_media_pipe_dockerfile_creates_appuser():
    content = _read_dockerfile("backend/media_pipe_service")
    assert "adduser" in content or "useradd" in content, (
        "media_pipe_service Dockerfile must create the appuser"
    )
