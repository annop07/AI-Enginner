"""Live demo of all three Week-1 capabilities against the configured LLM.

Run:  uv run python -m scripts.demo
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def test_chat() -> None:
    section("TEST 1  /chat  — agent picks tools by itself")
    r = client.post(
        "/chat",
        json={
            "message": "What is 1234 * 17? Also what time is it in Bangkok right now?"
        },
    )
    if r.status_code != 200:
        print("ERROR", r.status_code, r.text[:600])
        return
    d = r.json()
    print("ANSWER   :", d["answer"])
    print("ITERATIONS:", d["iterations"])
    print("TOKENS   :", d["usage"])
    print("TOOLS CALLED:")
    for t in d["tool_calls"]:
        print(f"   -> {t['tool']}({t['arguments']}) = {t['result']}")


def test_extract() -> None:
    section("TEST 2  /extract  — free text -> validated JSON")
    text = (
        "Standup with Aon and Beam. Aon needs to fix the login bug by Friday "
        "(high priority). Beam will draft the release notes next week."
    )
    r = client.post("/extract", json={"text": text})
    if r.status_code != 200:
        print("ERROR", r.status_code, r.text[:600])
        return
    import json

    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


def test_search() -> None:
    section("TEST 3  /knowledge/search  — semantic similarity search")
    r = client.post(
        "/knowledge/search",
        json={"query": "when is the office closed?", "top_k": 2},
    )
    if r.status_code != 200:
        print("ERROR", r.status_code, r.text[:600])
        return
    for h in r.json()["hits"]:
        print(f"   score={h['score']}  {h['text']}")


def show_usage() -> None:
    section("USAGE SUMMARY  /usage/summary")
    s = client.get("/usage/summary").json()
    print(f"   total requests : {s['total_requests']}")
    print(f"   total tokens   : {s['total_tokens']} "
          f"(prompt {s['total_prompt_tokens']} + completion {s['total_completion_tokens']})")
    print(f"   avg latency    : {s['avg_latency_ms']} ms")
    print(f"   by model       : {s['by_model']}")
    print("   -> open http://localhost:8000/dashboard for the full view")


if __name__ == "__main__":
    with client:  # triggers startup (init_db)
        test_chat()
        test_extract()
        test_search()
        show_usage()
