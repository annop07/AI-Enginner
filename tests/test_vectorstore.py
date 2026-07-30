"""Vector store test — uses an in-memory Qdrant, no API key needed.

fastembed downloads a small model on first run (~30MB), so this test may be
slow the very first time it executes.
"""
from __future__ import annotations

import pytest

from app.schemas import Document


@pytest.fixture
def store(monkeypatch, tmp_path):
    # Force in-memory Qdrant so tests never touch real data.
    from app import config, vectorstore

    config.get_settings.cache_clear()
    vectorstore.get_vector_store.cache_clear()
    monkeypatch.setenv("QDRANT_LOCATION", ":memory:")

    vs = vectorstore.VectorStore()
    yield vs


def test_add_and_search(store):
    store.add(
        [
            Document(text="Cats are small domesticated felines.", metadata={"k": "cat"}),
            Document(text="The Eiffel Tower is in Paris, France.", metadata={"k": "paris"}),
        ]
    )
    hits = store.search("Where is the Eiffel Tower?", top_k=1)
    assert len(hits) == 1
    assert "Paris" in hits[0].text
    assert hits[0].metadata.get("k") == "paris"
