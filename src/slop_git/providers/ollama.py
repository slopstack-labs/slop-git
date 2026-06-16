"""Ollama backend for local or self-hosted resolution.

Native HTTP transport against an Ollama ``/api/generate`` endpoint. No API key
is required for a local daemon; an optional bearer token is forwarded for
reverse-proxy authentication.
"""

from __future__ import annotations

from .base import Provider, post_json

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"


class OllamaProvider(Provider):
    """Routes resolution through a local (or self-hosted) Ollama instance."""

    name = "ollama"

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        *,
        max_tokens: int = 1024,
        host: str = DEFAULT_OLLAMA_URL,
    ):
        super().__init__(model, api_key, max_tokens=max_tokens)
        self.host = host

    def ready(self) -> bool:
        # A local daemon needs no credential; connectivity is validated on the
        # request itself, degrading to offline resolution on failure.
        return True

    def complete(self, system: str, prompt: str) -> str:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = post_json(
            self.host,
            {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
            },
            headers=headers,
        )
        return (data.get("response") or "").strip()
