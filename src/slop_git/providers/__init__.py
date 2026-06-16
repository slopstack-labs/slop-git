"""Pluggable inference backends.

A backend is selected by name (``settings.provider``) and constructed by
:func:`get_provider`. Each backend implements the :class:`Provider` contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .anthropic import AnthropicProvider
from .base import Provider, ProviderError
from .google import GoogleProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

if TYPE_CHECKING:  # avoid a runtime import cycle with config
    from ..config import Settings

# Provider-default models, applied when no model is explicitly configured.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o",
    "google": "gemini-2.0-flash",
    "ollama": "llama3",
}

_REGISTRY: dict[str, type[Provider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "ollama": OllamaProvider,
}


def resolve_model(provider: str, model: str) -> str:
    """Return the explicit model if set, else the provider default."""
    return model or DEFAULT_MODELS.get(provider, "")


def get_provider(settings: "Settings") -> Provider:
    """Construct the configured backend, or raise :class:`ProviderError`."""
    provider_cls = _REGISTRY.get(settings.provider)
    if provider_cls is None:
        raise ProviderError(
            f"unknown provider {settings.provider!r}; "
            f"choose from {sorted(_REGISTRY)}"
        )

    model = resolve_model(settings.provider, settings.model)
    if not model:
        raise ProviderError(f"no model configured for provider {settings.provider!r}")

    if settings.provider == "ollama":
        return OllamaProvider(
            model,
            settings.api_key,
            max_tokens=settings.max_tokens,
            host=settings.ollama_url,
        )
    return provider_cls(model, settings.api_key, max_tokens=settings.max_tokens)


__all__ = [
    "Provider",
    "ProviderError",
    "AnthropicProvider",
    "OpenAIProvider",
    "GoogleProvider",
    "OllamaProvider",
    "DEFAULT_MODELS",
    "resolve_model",
    "get_provider",
]
