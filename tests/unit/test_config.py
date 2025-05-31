"""
Unit tests for configuration settings classes:
- ValkeySettings
- GoogleAPISettings
- Settings (aggregated settings)

These tests verify:
- Default values when environment variables are not set.
- Correct parsing of environment variables into settings.
- Correct handling of secrets.
- Proper loading of combined settings.
"""

from pydantic import SecretStr
from ytindexer.config import GoogleAPISettings, Settings, ValkeySettings


def test_queue_settings_defaults(monkeypatch):
    """
    Test that ValkeySettings uses the correct default values when
    environment variables are not set.

    Defaults tested:
    - host: "localhost"
    - port: 6379
    - password: None
    """
    monkeypatch.delenv("VALKEY_HOST", raising=False)
    monkeypatch.delenv("VALKEY_PORT", raising=False)
    monkeypatch.delenv("VALKEY_PASSWORD", raising=False)

    settings = ValkeySettings()
    assert settings.host == "localhost"
    assert settings.port == 6379
    assert settings.password is None


def test_queue_settings_env(monkeypatch):
    """
    Test that ValkeySettings correctly reads values from environment variables:
    - VALKEY_HOST
    - VALKEY_PORT
    - VALKEY_PASSWORD
    """
    monkeypatch.setenv("VALKEY_HOST", "redis.local")
    monkeypatch.setenv("VALKEY_PORT", "6380")
    monkeypatch.setenv("VALKEY_PASSWORD", "s3cr3t")

    settings = ValkeySettings()
    assert settings.host == "redis.local"
    assert settings.port == 6380
    assert isinstance(settings.password, SecretStr)
    assert settings.password.get_secret_value() == "s3cr3t"


def test_google_api_settings_defaults(monkeypatch):
    """
    Test that GoogleAPISettings correctly uses values from environment variables:
    - GOOGLE_API_KEY
    - GOOGLE_API_URL
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "your-key")
    monkeypatch.setenv("GOOGLE_API_URL", "https://www.googleapis.com/youtube/v3/search")

    settings = GoogleAPISettings()
    assert settings.key == "your-key"
    assert str(settings.url) == "https://www.googleapis.com/youtube/v3/search"


def test_google_api_settings_env(monkeypatch):
    """
    Test that GoogleAPISettings correctly parses custom environment variables:
    - GOOGLE_API_KEY
    - GOOGLE_API_URL
    """
    monkeypatch.setenv("GOOGLE_API_KEY", "abc123")
    monkeypatch.setenv("GOOGLE_API_URL", "https://custom.api/google")

    settings = GoogleAPISettings()
    assert settings.key == "abc123"
    assert str(settings.url) == "https://custom.api/google"


def test_settings_combined(monkeypatch):
    """
    Test that the combined Settings class correctly loads nested settings
    from environment variables for both Valkey and GoogleAPI.

    Verifies:
    - Instances are of correct types (ValkeySettings, GoogleAPISettings).
    - Nested settings have the expected values.
    """
    monkeypatch.setenv("VALKEY_HOST", "localhost")
    monkeypatch.setenv("GOOGLE_API_KEY", "xyz")
    monkeypatch.setenv("GOOGLE_API_URL", "https://my.api")

    s = Settings.load_settings()
    assert isinstance(s.valkey, ValkeySettings)
    assert isinstance(s.googleapi, GoogleAPISettings)
    assert s.googleapi.key == "xyz"
    assert str(s.googleapi.url) == "https://my.api"
