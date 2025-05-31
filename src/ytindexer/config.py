"""
Configuration module defining settings for external services and application components.

This module contains Pydantic-based settings classes that load configuration
from environment variables (or a `.env` file) with appropriate prefixes.
It covers configuration for services such as Valkey, Google API, Ngrok, MongoDB,
and Elasticsearch.

Each settings class encapsulates related configuration parameters and provides
properties for commonly used connection strings (DSNs).

Example:
    To load all settings at once:
        settings = Settings.load_settings()
"""

from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ValkeySettings(BaseSettings):
    """
    Configuration settings for Valkey service.

    Attributes:
        host (str): Hostname for Valkey service. Defaults to "localhost".
        port (int): Port number for Valkey service. Defaults to 6379.
        password (Optional[SecretStr]): Optional password for authentication.
    """

    model_config = SettingsConfigDict(env=".env", env_prefix="VALKEY_")
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(6379, json_schema_extra={"env": "PORT"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})


class GoogleAPISettings(BaseSettings):
    """
    Configuration settings for Google API.

    Attributes:
        key (str): API key for Google services.
        url (str): Endpoint URL for the Google API.
    """

    model_config = SettingsConfigDict(env=".env", env_prefix="GOOGLE_API_")
    key: str = Field("your-key", json_schema_extra={"env": "KEY"})
    url: str = Field(
        "https://www.googleapis.com/youtube/v3/search", json_schema_extra={"env": "URL"}
    )


class NGrokSettings(BaseSettings):
    """
    Configuration settings for Ngrok service.

    Attributes:
        url (str): Ngrok public URL.
    """

    model_config = SettingsConfigDict(env=".env", env_prefix="NGROK_")
    url: str = Field("url", json_schema_extra={"env": "URL"})


class MongoSettings(BaseSettings):
    """
    Configuration settings for MongoDB connection.

    Attributes:
        name (str): Database name.
        host (str): MongoDB host.
        port (int): MongoDB port.
        username (Optional[str]): Username for authentication.
        password (Optional[SecretStr]): Password for authentication.
        auth (Optional[str]): Authentication database.
    """

    model_config = SettingsConfigDict(env=".env", env_prefix="MONGO_")
    name: str = Field("name", json_schema_extra={"env": "NAME"})
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(27017, json_schema_extra={"env": "PORT"})
    username: Optional[str] = Field(None, json_schema_extra={"env": "USERNAME"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})
    auth: Optional[str] = Field(None, json_schema_extra={"env": "AUTH"})

    @property
    def dsn(self) -> str:
        """
        Constructs the MongoDB DSN (Data Source Name) for connection.

        Returns:
            str: The full MongoDB connection string including credentials and auth source.
        """
        return f"mongodb://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/default_db?authSource={self.auth}"


class ElasticSettings(BaseSettings):
    """
    Configuration settings for Elasticsearch connection.

    Attributes:
        index_name (str): Name of the Elasticsearch index.
        host (str): Elasticsearch host.
        port (int): Elasticsearch port.
        username (Optional[str]): Username for authentication.
        password (Optional[SecretStr]): Password for authentication.
        scheme (str): Scheme used for connection (e.g., http, https).
    """

    model_config = SettingsConfigDict(env=".env", env_prefix="ELASTIC_")
    index_name: str = Field("videos", json_schema_extra={"env": "INDEX_NAME"})
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(9200, json_schema_extra={"env": "PORT"})
    username: Optional[str] = Field(None, json_schema_extra={"env": "USERNAME"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})
    scheme: str = Field("http", json_schema_extra={"env": "SCHEME"})

    @property
    def dsn(self) -> str:
        """
        Constructs the Elasticsearch DSN (Data Source Name) for connection.

        Returns:
            str: The full Elasticsearch connection URL including credentials.
        """
        return f"{self.scheme}://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}"


class Settings:
    """
    Aggregated application settings.

    Attributes:
        valkey (ValkeySettings): Settings for Valkey.
        googleapi (GoogleAPISettings): Settings for Google API.
        ngrok (NGrokSettings): Settings for Ngrok.
        mongo (MongoSettings): Settings for MongoDB.
        search (ElasticSettings): Settings for Elasticsearch.
    """

    def __init__(self):
        """Initialize settings by loading all individual configurations."""
        self.valkey = ValkeySettings()
        self.googleapi = GoogleAPISettings()
        self.ngrok = NGrokSettings()
        self.mongo = MongoSettings()
        self.search = ElasticSettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from environment variables or default values.

        Returns:
            Settings: An instance of Settings with all configs loaded.
        """
        return cls()


settings = Settings()
