"""Token-usage tracking, backed by SQLite (stdlib, zero extra deps).

Every LLM-backed request records one row: which endpoint, which model,
how many tokens (prompt / completion / total), how many LLM round-trips,
and how long it took. The dashboard reads aggregates from here.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import (
    EndpointUsage,
    ModelUsage,
    TimePoint,
    UsageEvent,
    UsageSummary,
)

DB_PATH = Path("./data/usage.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                ts                TEXT    NOT NULL,
                endpoint          TEXT    NOT NULL,
                model             TEXT    NOT NULL,
                prompt_tokens     INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens      INTEGER NOT NULL,
                llm_calls         INTEGER NOT NULL,
                latency_ms        INTEGER NOT NULL
            )
            """
        )


def record(
    *,
    endpoint: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    llm_calls: int,
    latency_ms: int,
) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO usage_events
                (ts, endpoint, model, prompt_tokens, completion_tokens,
                 total_tokens, llm_calls, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now_iso(),
                endpoint,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                llm_calls,
                latency_ms,
            ),
        )


def summary(recent_limit: int = 15) -> UsageSummary:
    with _conn() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*)                       AS total_requests,
                COALESCE(SUM(prompt_tokens),0)     AS p,
                COALESCE(SUM(completion_tokens),0) AS c,
                COALESCE(SUM(total_tokens),0)      AS t,
                COALESCE(AVG(latency_ms),0)        AS lat
            FROM usage_events
            """
        ).fetchone()

        by_model = [
            ModelUsage(
                model=r["model"], requests=r["requests"], total_tokens=r["total_tokens"]
            )
            for r in conn.execute(
                """
                SELECT model, COUNT(*) AS requests,
                       SUM(total_tokens) AS total_tokens
                FROM usage_events GROUP BY model ORDER BY total_tokens DESC
                """
            ).fetchall()
        ]

        by_endpoint = [
            EndpointUsage(
                endpoint=r["endpoint"],
                requests=r["requests"],
                total_tokens=r["total_tokens"],
            )
            for r in conn.execute(
                """
                SELECT endpoint, COUNT(*) AS requests,
                       SUM(total_tokens) AS total_tokens
                FROM usage_events GROUP BY endpoint ORDER BY total_tokens DESC
                """
            ).fetchall()
        ]

        # Group by minute so a live demo actually shows movement.
        timeseries = [
            TimePoint(
                bucket=r["bucket"],
                total_tokens=r["total_tokens"],
                requests=r["requests"],
            )
            for r in conn.execute(
                """
                SELECT substr(ts, 1, 16) AS bucket,
                       SUM(total_tokens) AS total_tokens,
                       COUNT(*) AS requests
                FROM usage_events GROUP BY bucket ORDER BY bucket
                """
            ).fetchall()
        ]

        recent = [
            UsageEvent(**dict(r))
            for r in conn.execute(
                "SELECT * FROM usage_events ORDER BY id DESC LIMIT ?",
                (recent_limit,),
            ).fetchall()
        ]

    return UsageSummary(
        total_requests=totals["total_requests"],
        total_prompt_tokens=totals["p"],
        total_completion_tokens=totals["c"],
        total_tokens=totals["t"],
        avg_latency_ms=round(totals["lat"], 1),
        by_model=by_model,
        by_endpoint=by_endpoint,
        timeseries=timeseries,
        recent=recent,
    )
