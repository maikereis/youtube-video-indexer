from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ValkeySettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="VALKEY_")
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(6379, json_schema_extra={"env": "PORT"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})

class GoogleAPISettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="GOOGLE_API_")
    key: str = Field("your-key", json_schema_extra={"env": "KEY"})
    url: str = Field("https://www.googleapis.com/youtube/v3/search", json_schema_extra={"env": "URL"})

class NGrokSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="NGROK_")
    url: str = Field("url", json_schema_extra={"env": "URL"})

class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="MONGO_")
    name: str = Field("name", json_schema_extra={"env": "NAME"})
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(27017, json_schema_extra={"env": "PORT"})
    username: Optional[str] = Field(None, json_schema_extra={"env": "USERNAME"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})
    auth: Optional[str] = Field(None, json_schema_extra={"env": "AUTH"})

    @property
    def dsn(self) -> str:
        return f"mongodb://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}/default_db?authSource={self.auth}"

class ElasticSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="ELASTIC_")
    index_name: str = Field("videos", json_schema_extra={"env": "INDEX_NAME"})
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(9200, json_schema_extra={"env": "PORT"})
    username: Optional[str] = Field(None, json_schema_extra={"env": "USERNAME"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})
    scheme: str = Field("http", json_schema_extra={"env": "SCHEME"})

    @property
    def dsn(self) -> str:
        return f"{self.scheme}://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}"

class Settings:
    def __init__(self):
        self.valkey = ValkeySettings()
        self.googleapi = GoogleAPISettings()
        self.ngrok = NGrokSettings()
        self.mongo = MongoSettings()
        self.search = ElasticSettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from environment variables or defaults.
        """
        return cls()

settings = Settings()