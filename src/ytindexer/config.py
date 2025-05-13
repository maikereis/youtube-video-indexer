from typing  import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class QueueSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="QUEUE_")
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(6379, json_schema_extra={"env": "PORT"})
    username: Optional[str] = Field(None, json_schema_extra={"env": "USERNAME"})
    password: Optional[SecretStr] = Field(None, json_schema_extra={"env": "PASSWORD"})

class GoogleAPISettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="GOOGLE_API_")
    key: str = Field("your-key", json_schema_extra={"env": "KEY"})
    url: str = Field("https://www.googleapis.com/youtube/v3/search", json_schema_extra={"env": "URL"})

class Settings:
    def __init__(self):
        self.queue = QueueSettings()
        self.googleapi = GoogleAPISettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from environment variables or defaults.
        """
        return cls()

settings = Settings()