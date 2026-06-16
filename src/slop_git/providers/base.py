"""Provider interface and shared transport for the inference layer.

Every backend implements a single method — :meth:`Provider.complete` — which
takes a system directive plus a user prompt and returns resolved text. This
mirrors the one-method-per-backend contract used across the SlopStack tooling
stack and keeps the dispatch surface minimal.
"""

from __future__ import annotations

import abc
import json
import urllib.error
import urllib.request
from typing import Any, Mapping

# Maximum wall-clock duration for a single inference round-trip (seconds).
DEFAULT_HTTP_TIMEOUT = 300


class ProviderError(RuntimeError):
    """Raised when a backend cannot be constructed, configured, or reached."""


class Provider(abc.ABC):
    """Streaming-agnostic completion backend.

    Implementations own their transport, authentication, and response decoding.
    Construction is cheap; readiness (credentials, optional SDK availability) is
    resolved lazily via :meth:`ready`.
    """

    name: str = "provider"

    def __init__(self, model: str, api_key: str | None = None, *, max_tokens: int = 1024):
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens

    @abc.abstractmethod
    def ready(self) -> bool:
        """Return True if this backend can service a request right now."""

    @abc.abstractmethod
    def complete(self, system: str, prompt: str) -> str:
        """Resolve ``prompt`` under ``system`` and return the decoded text."""


def post_json(
    url: str,
    payload: Mapping[str, Any],
    headers: Mapping[str, str] | None = None,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
) -> dict[str, Any]:
    """POST a JSON body and decode a JSON response via the standard library.

    The OpenAI, Gemini, and Ollama backends use this native transport so they
    pull in no third-party HTTP dependency. Non-2xx responses and connection
    failures are surfaced as :class:`ProviderError`.
    """
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for header_name, header_value in (headers or {}).items():
        request.add_header(header_name, header_value)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise ProviderError(f"{_origin(url)} returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise ProviderError(f"cannot reach {_origin(url)}: {error.reason}") from error


def _origin(url: str) -> str:
    """Strip query parameters so credentials never reach logs or error text."""
    return url.split("?", 1)[0]
