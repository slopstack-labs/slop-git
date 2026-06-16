"""OpenAI Chat Completions backend.

Native HTTP transport — requires only an API key, no additional dependency.
"""

from __future__ import annotations

import os

from .base import Provider, post_json

_ENDPOINT = "https://api.openai.com/v1/chat/completions"
_ENV_KEYS = ("OPENAI_API_KEY",)


class OpenAIProvider(Provider):
    """Routes resolution through the OpenAI Chat Completions API."""

    name = "openai"

    def _key(self) -> str | None:
        return self.api_key or next(
            (os.getenv(key) for key in _ENV_KEYS if os.getenv(key)), None
        )

    def ready(self) -> bool:
        return bool(self._key())

    def complete(self, system: str, prompt: str) -> str:
        data = post_json(
            _ENDPOINT,
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            headers={"Authorization": f"Bearer {self._key()}"},
        )
        return data["choices"][0]["message"]["content"].strip()
