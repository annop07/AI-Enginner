"""Usage-store tests — pure SQLite, no API key needed."""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def usage(monkeypatch, tmp_path):
    from app import usage as usage_mod

    # Point the DB at a temp file so tests are isolated.
    monkeypatch.setattr(usage_mod, "DB_PATH", tmp_path / "usage.db")
    usage_mod.init_db()
    return usage_mod


def test_record_and_summary(usage):
    usage.record(
        endpoint="/chat", model="gpt-x", prompt_tokens=100,
        completion_tokens=40, total_tokens=140, llm_calls=2, latency_ms=1200,
    )
    usage.record(
        endpoint="/extract", model="gpt-x", prompt_tokens=50,
        completion_tokens=10, total_tokens=60, llm_calls=1, latency_ms=800,
    )
    s = usage.summary()
    assert s.total_requests == 2
    assert s.total_tokens == 200
    assert s.total_prompt_tokens == 150
    assert s.avg_latency_ms == 1000.0
    # one model, two endpoints
    assert len(s.by_model) == 1 and s.by_model[0].total_tokens == 200
    assert {e.endpoint for e in s.by_endpoint} == {"/chat", "/extract"}
    assert len(s.recent) == 2


def test_empty_summary(usage):
    s = usage.summary()
    assert s.total_requests == 0
    assert s.total_tokens == 0
    assert s.recent == []
