import os

import pytest
from pydantic import SecretStr

from ytindexer.config import GoogleAPISettings, ValkeySettings, Settings


def test_queue_settings_defaults(monkeypatch):
    monkeypatch.delenv("VALKEY_HOST", raising=False)
    monkeypatch.delenv("VALKEY_PORT", raising=False)
    monkeypatch.delenv("VALKEY_PASSWORD", raising=False)

    settings = ValkeySettings()
    assert settings.host == "localhost"
    assert settings.port == 6379
    assert settings.password is None

def test_queue_settings_env(monkeypatch):
    monkeypatch.setenv("VALKEY_HOST", "redis.local")
    monkeypatch.setenv("VALKEY_PORT", "6380")
    monkeypatch.setenv("VALKEY_PASSWORD", "s3cr3t")

    settings = ValkeySettings()
    assert settings.host == "redis.local"
    assert settings.port == 6380
    assert isinstance(settings.password, SecretStr)
    assert settings.password.get_secret_value() == "s3cr3t"

def test_google_api_settings_defaults(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "your-key")
    monkeypatch.setenv("GOOGLE_API_URL", "https://www.googleapis.com/youtube/v3/search")

    settings = GoogleAPISettings()
    assert settings.key == "your-key"
    assert str(settings.url) == "https://www.googleapis.com/youtube/v3/search"

def test_google_api_settings_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "abc123")
    monkeypatch.setenv("GOOGLE_API_URL", "https://custom.api/google")

    settings = GoogleAPISettings()
    assert settings.key == "abc123"
    assert str(settings.url) == "https://custom.api/google"

def test_settings_combined(monkeypatch):
    monkeypatch.setenv("VALKEY_HOST", "localhost")
    monkeypatch.setenv("GOOGLE_API_KEY", "xyz")
    monkeypatch.setenv("GOOGLE_API_URL", "https://my.api")

    s = Settings.load_settings()
    assert isinstance(s.valkey, ValkeySettings)
    assert isinstance(s.googleapi, GoogleAPISettings)
    assert s.googleapi.key == "xyz"
    assert str(s.googleapi.url) == "https://my.api"
