import pytest

from a_stock_agent.config import Settings
from a_stock_agent.llm import build_model_config


def test_default_akshare_proxy_patch_urls_match_eastmoney_allowlist():
    settings = Settings(_env_file=None)

    assert settings.akshare_proxy_patch_hook_urls == [
        "https://82.push2.eastmoney.com/api/qt/clist/get",
        "https://push2.eastmoney.com/api/qt/stock/get",
        "https://17.push2.eastmoney.com/api/qt/clist/get",
        "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "https://push2his.eastmoney.com/api/qt/stock/trends2/get",
        "https://push2.eastmoney.com/api/qt/clist/get",
        "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
        "http://push2.eastmoney.com/api/qt/clist/get",
    ]


def test_akshare_proxy_patch_hook_urls_can_be_overridden(monkeypatch):
    monkeypatch.setenv(
        "AKSHARE_PROXY_PATCH_HOOK_URLS",
        "https://example.test/a, https://example.test/b",
    )

    settings = Settings(_env_file=None)

    assert settings.akshare_proxy_patch_hook_urls == [
        "https://example.test/a",
        "https://example.test/b",
    ]


def test_legacy_anthropic_env_from_go_demo_is_supported(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "legacy-secret")
    monkeypatch.setenv("ANTHROPIC_MODEL", "MiniMax-M2.7-highspeed")

    settings = Settings(_env_file=None)
    model_config = build_model_config(settings)

    assert settings.llm_provider == "anthropic"
    assert model_config.model == "anthropic/MiniMax-M2.7-highspeed"
    assert model_config.api_base == "https://api.minimaxi.com/anthropic"
    assert model_config.api_key == "legacy-secret"


def test_openai_compatible_config_maps_to_litellm_model_name():
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        llm_model="MiniMax-M2.7",
        llm_base_url="https://api.example.com/v1",
        llm_api_key="secret",
    )

    model_config = build_model_config(settings)

    assert model_config.provider == "openai"
    assert model_config.model == "openai/MiniMax-M2.7"
    assert model_config.api_base == "https://api.example.com/v1"
    assert model_config.api_key == "secret"


def test_anthropic_compatible_config_uses_auth_token_fallback():
    settings = Settings(
        _env_file=None,
        llm_provider="anthropic",
        llm_model="MiniMax-M2.7-highspeed",
        llm_base_url="https://api.minimaxi.com/anthropic",
        llm_auth_token="token",
    )

    model_config = build_model_config(settings)

    assert model_config.provider == "anthropic"
    assert model_config.model == "anthropic/MiniMax-M2.7-highspeed"
    assert model_config.api_key == "token"


def test_llm_config_requires_api_secret():
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        llm_model="MiniMax-M2.7",
        llm_base_url="https://api.example.com/v1",
    )

    with pytest.raises(ValueError, match="LLM_API_KEY"):
        build_model_config(settings)
