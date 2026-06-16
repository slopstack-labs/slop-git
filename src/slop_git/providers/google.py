"""Google Gemini backend.

Native HTTP transport against the Generative Language API. The API key is passed
as a query parameter and is stripped from any surfaced error text.
"""

from __future__ import annotations

import os

from .base import Provider, post_json

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_ENV_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


class GoogleProvider(Provider):
    """Routes resolution through the Gemini ``generateContent`` endpoint."""

    name = "google"

    def _key(self) -> str | None:
        return self.api_key or next(
            (os.getenv(key) for key in _ENV_KEYS if os.getenv(key)), None
        )

    def ready(self) -> bool:
        return bool(self._key())

    def complete(self, system: str, prompt: str) -> str:
        url = f"{_BASE}/{self.model}:generateContent?key={self._key()}"
        data = post_json(
            url,
            {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": prompt}]}],
            },
        )
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
