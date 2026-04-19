from pathlib import Path
from typing import Annotated, Any

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
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
    akshare_proxy_patch_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("akshare_proxy_patch_enabled", "AKSHARE_PROXY_PATCH_ENABLED"),
    )
    akshare_proxy_patch_gateway: str = Field(
        default="101.201.173.125",
        validation_alias=AliasChoices("akshare_proxy_patch_gateway", "AKSHARE_PROXY_PATCH_GATEWAY"),
    )
    akshare_proxy_patch_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("akshare_proxy_patch_token", "AKSHARE_PROXY_PATCH_TOKEN"),
    )
    akshare_proxy_patch_retry: int = Field(
        default=30,
        validation_alias=AliasChoices("akshare_proxy_patch_retry", "AKSHARE_PROXY_PATCH_RETRY"),
    )
    akshare_proxy_patch_hook_urls: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "https://82.push2.eastmoney.com/api/qt/clist/get",
            "https://push2.eastmoney.com/api/qt/stock/get",
            "https://17.push2.eastmoney.com/api/qt/clist/get",
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            "https://push2his.eastmoney.com/api/qt/stock/trends2/get",
            "https://push2.eastmoney.com/api/qt/clist/get",
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
            "http://push2.eastmoney.com/api/qt/clist/get",
        ],
        validation_alias=AliasChoices("akshare_proxy_patch_hook_urls", "AKSHARE_PROXY_PATCH_HOOK_URLS"),
    )

    @field_validator("akshare_proxy_patch_hook_urls", mode="before")
    @classmethod
    def parse_akshare_proxy_patch_hook_urls(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

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
            "akshare_proxy_patch_hook_domains": "akshare_proxy_patch_hook_urls",
        }
        for old_key, new_key in aliases.items():
            if not data.get(new_key) and data.get(old_key):
                data[new_key] = data[old_key]
        if any(data.get(key) for key in aliases):
            data.setdefault("llm_provider", "anthropic")
        return data


def get_settings() -> Settings:
    return Settings()
