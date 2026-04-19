import pytest

from a_stock_agent.config import Settings
from a_stock_agent.llm import build_model_config


def test_openai_compatible_config_maps_to_litellm_model_name():
    settings = Settings(
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
        llm_provider="openai",
        llm_model="MiniMax-M2.7",
        llm_base_url="https://api.example.com/v1",
    )

    with pytest.raises(ValueError, match="LLM_API_KEY"):
        build_model_config(settings)
