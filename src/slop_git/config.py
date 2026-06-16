"""Runtime configuration for the narrative version control layer.

By default slop-git resolves operations **offline**, against a local vibes
engine, so the package is fully functional without network access or
credentials. Enable live resolution with ``live=True`` and select a backend
with ``provider=...``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    """Global configuration for narrative version control resolution."""

    # Inference backend: "anthropic" (default), "openai", "google", or "ollama".
    provider: str = os.environ.get("SLOP_GIT_PROVIDER", "anthropic")

    # Model identifier. Empty selects the provider default (e.g. claude-opus-4-8
    # for Anthropic, gpt-4o for OpenAI).
    model: str = os.environ.get("SLOP_GIT_MODEL", "")

    # Credential for the selected backend. Falls back to the backend's native
    # environment variable (ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY).
    api_key: str | None = os.environ.get("SLOP_GIT_API_KEY")

    # Endpoint for the local Ollama backend.
    ollama_url: str = os.environ.get(
        "SLOP_GIT_OLLAMA_URL", "http://localhost:11434/api/generate"
    )

    # When False (default), operations are resolved by the offline local engine.
    # Set live=True (or SLOP_GIT_LIVE=1) to route through the configured
    # backend. Any backend failure degrades cleanly back to offline resolution.
    live: bool = _env_flag("SLOP_GIT_LIVE", False)

    # Token budget per resolved narrative operation.
    max_tokens: int = int(os.environ.get("SLOP_GIT_MAX_TOKENS", "512"))

    # When True (default), hallucinated merge results are written to a
    # `.slop_merge` file rather than overwriting the original conflicted file.
    # Set to False only if you are certain you want the narrative synthesis
    # to replace your code directly, which you should not be.
    safe_merge: bool = _env_flag("SLOP_GIT_SAFE_MERGE", True)

    # CPU% threshold above which commit messages shift to "high stress" pool.
    # Below this threshold, messages are "medium stress". Below 30%, "low".
    stress_threshold: int = int(os.environ.get("SLOP_GIT_STRESS_THRESHOLD", "70"))


settings = Settings()


def configure(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    ollama_url: str | None = None,
    live: bool | None = None,
    max_tokens: int | None = None,
    safe_merge: bool | None = None,
    stress_threshold: int | None = None,
) -> Settings:
    """Update the global configuration in place and return it.

    Example::

        import slop_git
        slop_git.configure(provider="openai", live=True)
    """
    if provider is not None:
        settings.provider = provider
    if model is not None:
        settings.model = model
    if api_key is not None:
        settings.api_key = api_key
    if ollama_url is not None:
        settings.ollama_url = ollama_url
    if live is not None:
        settings.live = live
    if max_tokens is not None:
        settings.max_tokens = max_tokens
    if safe_merge is not None:
        settings.safe_merge = safe_merge
    if stress_threshold is not None:
        settings.stress_threshold = stress_threshold
    return settings
