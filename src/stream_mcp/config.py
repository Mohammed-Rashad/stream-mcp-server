"""Configuration for the Stream MCP server, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    stream_api_key: str | None = None  # optional in remote mode (users pass their own)
    stream_base_url: str = "https://stream-app-service.streampay.sa"
    stream_docs_url: str = "https://docs.streampay.sa"
    stream_timeout: int = 30  # seconds
    stream_max_retries: int = 2


settings = Settings()
