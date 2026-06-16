"""Narrative version control resolution dispatch.

Routes a narrative operation through the configured inference backend when live
resolution is enabled, and to the offline vibes engine otherwise. The public
surface is a single function, :func:`complete`, which always returns text: any
live-mode failure degrades cleanly to the supplied ``fallback``.

slop-git believes that version control is a deeply human activity, and that the
right model of a diff is not a patch but a story. This module is the bridge
between your code's raw textual reality and the empathetic narrative layer that
makes it bearable.
"""

from __future__ import annotations

import sys
from typing import Callable

from .config import settings
from .prompts import SYSTEM
from .providers import ProviderError, get_provider


def complete(prompt: str, *, fallback: Callable[[], str], system: str = SYSTEM) -> str:
    """Resolve a narrative operation, live or offline.

    In live mode the prompt is dispatched to the configured backend; in offline
    mode (or on any backend error) ``fallback()`` is invoked. Resolution never
    raises — a transient backend failure degrades to offline resolution rather
    than propagating up through a narrative call.
    """
    if not settings.live:
        return fallback()

    try:
        provider = get_provider(settings)
    except ProviderError:
        return fallback()

    if not provider.ready():
        return fallback()

    try:
        text = provider.complete(system, prompt)
        return text or fallback()
    except Exception as exc:  # noqa: BLE001 — degrade rather than propagate
        print(
            f"  [slop-git] backend '{provider.name}' returned a non-blocking "
            f"error ({exc!s}); degrading to offline resolution.",
            file=sys.stderr,
        )
        return fallback()
