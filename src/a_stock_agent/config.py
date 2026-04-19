from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "a-stock-agent"
    environment: str = "development"

    database_path: Path = Path("data/a_stock_agent.sqlite3")
    books_dir: Path = Path("books")
    models_dir: Path = Path("data/models")

    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    embedding_dimensions: int = 768

    llm_provider: str = Field(default="anthropic")
    llm_model: str = Field(default="MiniMax-M2.7-highspeed")
    llm_base_url: str | None = Field(default="https://api.minimaxi.com/anthropic")
    llm_api_key: str | None = None
    llm_auth_token: str | None = None

    enable_live_akshare: bool = True
    enable_adk_web_ui: bool = False


def get_settings() -> Settings:
    return Settings()
