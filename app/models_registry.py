"""Discovery of the models the configured LLM endpoint offers.

The endpoint is OpenAI-compatible, so `client.models.list()` works against
OpenAI itself as well as proxies like KKU IntelSphere. The list barely ever
changes, so it is cached for a few minutes rather than fetched per request.
"""
from __future__ import annotations

import time

from openai import OpenAI

from app.config import get_settings

_CACHE_TTL_SECONDS = 300
_cache: tuple[float, list[str]] | None = None


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_configured:
        raise RuntimeError("OPENAI_API_KEY is not set. See .env.example.")
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def list_models(force_refresh: bool = False) -> list[str]:
    """Model ids offered by the endpoint, sorted. Cached for a few minutes."""
    global _cache
    now = time.monotonic()
    if not force_refresh and _cache is not None and now - _cache[0] < _CACHE_TTL_SECONDS:
        return _cache[1]

    models = sorted(m.id for m in _client().models.list().data)
    _cache = (now, models)
    return models


def is_known(model: str) -> bool:
    """Whether `model` is offered by the endpoint.

    Fails open: if discovery itself breaks, we let the request through and let
    the actual completion call be the judge, rather than blocking a valid model
    because a listing call happened to fail.
    """
    try:
        return model in list_models()
    except Exception:  # noqa: BLE001
        return True
