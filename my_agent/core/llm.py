from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
import os
from my_agent.core.infisical_client import aget_secret

_cached_api_keys: dict[str, str] = {}

_PROVIDER_MAP = {
    "gemini": ("google_genai", "GEMINI_API_KEY"),
    "gpt-":   ("openai",       "OPENAI_API_KEY"),
    "o1":     ("openai",       "OPENAI_API_KEY"),
    "o3":     ("openai",       "OPENAI_API_KEY"),
    "o4":     ("openai",       "OPENAI_API_KEY"),
    "claude": ("anthropic",    "ANTHROPIC_API_KEY"),
}

def _resolve_provider(model: str) -> tuple[str, str]:
    for prefix, (provider, secret) in _PROVIDER_MAP.items():
        if model.lower().startswith(prefix):
            return provider, secret
    return "openai", "OPENAI_API_KEY"

async def _get_api_key(model: str) -> str:
    global _cached_api_keys
    provider, secret_name = _resolve_provider(model)
    
    # Check environment first
    env_key = os.environ.get(secret_name)
    if env_key:
        return env_key

    if provider not in _cached_api_keys:
        secret = await aget_secret(secret_name)
        if secret:
            _cached_api_keys[provider] = secret
    
    return _cached_api_keys.get(provider, "")

async def get_llm(
    model: str = "gpt-4o",
    temperature: float = 0,
) -> BaseChatModel:
    api_key = await _get_api_key(model)
    provider, _ = _resolve_provider(model)

    return init_chat_model(
        model=model,
        model_provider=provider,
        api_key=api_key,
        temperature=temperature,
    )
