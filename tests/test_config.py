import os
import pytest
from pydantic import SecretStr
from ytindexer.config import QueueSettings, GoogleAPISettings, Settings


def test_queue_settings_defaults(monkeypatch):
    monkeypatch.delenv("QUEUE_HOST", raising=False)
    monkeypatch.delenv("QUEUE_PORT", raising=False)
    monkeypatch.delenv("QUEUE_USERNAME", raising=False)
    monkeypatch.delenv("QUEUE_PASSWORD", raising=False)

    settings = QueueSettings()
    assert settings.host == "localhost"
    assert settings.port == 6379
    assert settings.username is None
    assert settings.password is None

def test_queue_settings_env(monkeypatch):
    monkeypatch.setenv("QUEUE_HOST", "redis.local")
    monkeypatch.setenv("QUEUE_PORT", "6380")
    monkeypatch.setenv("QUEUE_USERNAME", "admin")
    monkeypatch.setenv("QUEUE_PASSWORD", "s3cr3t")

    settings = QueueSettings()
    assert settings.host == "redis.local"
    assert settings.port == 6380
    assert settings.username == "admin"
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
    monkeypatch.setenv("QUEUE_HOST", "localhost")
    monkeypatch.setenv("GOOGLE_API_KEY", "xyz")
    monkeypatch.setenv("GOOGLE_API_URL", "https://my.api")

    s = Settings.load_settings()
    assert isinstance(s.queue, QueueSettings)
    assert isinstance(s.googleapi, GoogleAPISettings)
    assert s.googleapi.key == "xyz"
    assert str(s.googleapi.url) == "https://my.api"
