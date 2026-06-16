"""Anthropic Claude backend (default).

Uses the official ``anthropic`` SDK. Install via the ``[anthropic]`` extra.
"""

from __future__ import annotations

import os

from .base import Provider

_ENV_KEYS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


class AnthropicProvider(Provider):
    """Routes resolution through Anthropic's Messages API."""

    name = "anthropic"

    def _credentialed(self) -> bool:
        return bool(self.api_key or any(os.getenv(key) for key in _ENV_KEYS))

    def ready(self) -> bool:
        if not self._credentialed():
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def complete(self, system: str, prompt: str) -> str:
        import anthropic

        client = (
            anthropic.Anthropic(api_key=self.api_key)
            if self.api_key
            else anthropic.Anthropic()
        )
        # Sampling temperature is not exposed: response variance is an intrinsic
        # property of the resolution model, not a tunable parameter.
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
