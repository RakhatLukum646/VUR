import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_BASE_ENV = {
    "mongodb_url": "mongodb://localhost:27017",
    "mongodb_db": "vur_test",
    "email_host": "smtp.example.com",
    "email_port": "587",
    "email_user": "noreply@example.com",
    "email_password": "password",
    "frontend_url": "http://localhost:5173",
}


def _reload_config_module():
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.config")


def test_settings_raises_when_jwt_secret_is_default(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "change-me-in-production")

    with pytest.raises(Exception, match="(?i)jwt_secret|insecure"):
        _reload_config_module()


def test_settings_raises_when_jwt_secret_is_too_short(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "tooshort")

    with pytest.raises(Exception, match="(?i)jwt_secret|32"):
        _reload_config_module()


def test_settings_raises_when_jwt_secret_is_empty(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "")

    with pytest.raises(Exception):
        _reload_config_module()


def test_settings_raises_when_jwt_secret_is_changeme_variant(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "changeme")

    with pytest.raises(Exception):
        _reload_config_module()


def test_settings_accepts_strong_jwt_secret(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "a" * 32)

    config_module = _reload_config_module()
    assert len(config_module.settings.jwt_secret) >= 32


def test_settings_accepts_long_random_jwt_secret(monkeypatch):
    for k, v in _BASE_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("jwt_secret", "super-random-jwt-secret-key-for-testing-only")

    config_module = _reload_config_module()
    assert config_module.settings.jwt_secret == "super-random-jwt-secret-key-for-testing-only"
