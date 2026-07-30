"""Model-selection tests — no API key needed (the registry is stubbed)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import models_registry
from app.main import _resolve_model, app


@pytest.fixture
def known_models(monkeypatch):
    monkeypatch.setattr(
        models_registry, "list_models", lambda force_refresh=False: ["a-1", "b-2"]
    )


def test_resolve_falls_back_to_default(known_models):
    from app.config import get_settings

    assert _resolve_model(None) == get_settings().llm_model
    assert _resolve_model("") == get_settings().llm_model


def test_resolve_accepts_known_model(known_models):
    assert _resolve_model("a-1") == "a-1"


def test_resolve_rejects_unknown_model(known_models):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        _resolve_model("nope")
    assert exc.value.status_code == 400


def test_unknown_model_is_400_not_500(known_models):
    with TestClient(app) as client:
        r = client.post("/chat", json={"message": "hi", "model": "nope"})
    assert r.status_code == 400
    assert "nope" in r.json()["detail"]


def test_is_known_fails_open_when_discovery_breaks(monkeypatch):
    """A listing outage must not block an otherwise valid model."""

    def boom(force_refresh: bool = False):
        raise RuntimeError("endpoint down")

    monkeypatch.setattr(models_registry, "list_models", boom)
    assert models_registry.is_known("anything") is True
