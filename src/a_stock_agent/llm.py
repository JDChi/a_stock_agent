from dataclasses import dataclass
from typing import Any

from .config import Settings


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    api_base: str
    api_key: str


def build_model_config(settings: Settings) -> ModelConfig:
    provider = settings.llm_provider.strip().lower()
    if provider not in {"openai", "anthropic"}:
        raise ValueError("LLM_PROVIDER must be 'openai' or 'anthropic'")
    if not settings.llm_model:
        raise ValueError("LLM_MODEL is required")
    if not settings.llm_base_url:
        raise ValueError("LLM_BASE_URL is required")

    api_key = settings.llm_api_key or settings.llm_auth_token
    if not api_key:
        raise ValueError("LLM_API_KEY or LLM_AUTH_TOKEN is required")

    prefix = "openai" if provider == "openai" else "anthropic"
    model_name = settings.llm_model
    if not model_name.startswith(f"{prefix}/"):
        model_name = f"{prefix}/{model_name}"

    return ModelConfig(
        provider=provider,
        model=model_name,
        api_base=settings.llm_base_url,
        api_key=api_key,
    )


def create_litellm_model(settings: Settings) -> Any:
    model_config = build_model_config(settings)
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:
        raise RuntimeError("google-adk LiteLlm connector is not installed") from exc

    return LiteLlm(
        model=model_config.model,
        api_base=model_config.api_base,
        api_key=model_config.api_key,
    )
