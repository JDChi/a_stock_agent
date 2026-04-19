from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, model_validator
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

    llm_provider: str = Field(
        default="anthropic",
        validation_alias=AliasChoices("llm_provider", "LLM_PROVIDER"),
    )
    llm_model: str = Field(
        default="MiniMax-M2.7-highspeed",
        validation_alias=AliasChoices("llm_model", "LLM_MODEL", "ANTHROPIC_MODEL"),
    )
    llm_base_url: str | None = Field(
        default="https://api.minimaxi.com/anthropic",
        validation_alias=AliasChoices("llm_base_url", "LLM_BASE_URL", "ANTHROPIC_BASE_URL"),
    )
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("llm_api_key", "LLM_API_KEY", "ANTHROPIC_API_KEY"),
    )
    llm_auth_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("llm_auth_token", "LLM_AUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN"),
    )

    enable_live_akshare: bool = True
    enable_adk_web_ui: bool = False
    akshare_proxy_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("akshare_proxy_url", "AKSHARE_PROXY_URL"),
    )
    akshare_disable_system_proxy: bool = Field(
        default=True,
        validation_alias=AliasChoices("akshare_disable_system_proxy", "AKSHARE_DISABLE_SYSTEM_PROXY"),
    )

    @model_validator(mode="before")
    @classmethod
    def support_legacy_anthropic_env(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        aliases = {
            "anthropic_base_url": "llm_base_url",
            "anthropic_api_key": "llm_api_key",
            "anthropic_auth_token": "llm_auth_token",
            "anthropic_model": "llm_model",
        }
        for old_key, new_key in aliases.items():
            if not data.get(new_key) and data.get(old_key):
                data[new_key] = data[old_key]
        if any(data.get(key) for key in aliases):
            data.setdefault("llm_provider", "anthropic")
        return data


def get_settings() -> Settings:
    return Settings()
