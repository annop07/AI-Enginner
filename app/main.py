"""FastAPI microservice exposing the AI agent + a usage dashboard.

Endpoints
  GET  /                → service metadata
  GET  /health          → liveness + config/vector-store status
  GET  /tools           → the tool specs the agent can call
  POST /chat            → run the tool-calling agent (records token usage)
  POST /extract         → structured output via Instructor (records token usage)
  POST /knowledge/seed  → add documents to the vector DB
  POST /knowledge/search→ raw similarity search
  GET  /usage/summary   → aggregated token/cost stats (JSON)
  GET  /dashboard       → the HTML usage dashboard
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAIError

from app import models_registry, usage
from app.agent import run_agent
from app.config import get_settings
from app.extractor import extract_meeting_notes
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ExtractRequest,
    MeetingNotes,
    SearchRequest,
    SearchResponse,
    SeedRequest,
    UsageSummary,
)
from app.tools import get_openai_tool_specs
from app.vectorstore import get_vector_store

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    usage.init_db()
    yield


app = FastAPI(
    title="AI Agent Service",
    version="0.2.0",
    description="Week 1 Bootcamp: tool-calling agent + structured output + vector search + token dashboard.",
    lifespan=lifespan,
)

# Allow the Next.js dev frontend (and any local origin) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    settings = get_settings()
    return {
        "service": "ai-agent-service",
        "version": "0.2.0",
        "model": settings.llm_model,
        "dashboard": "/dashboard",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    store = get_vector_store()
    return {
        "status": "ok",
        "model": settings.llm_model,
        "openai_configured": settings.openai_configured,
        "vector_documents": store.count(),
        "tools": [t["function"]["name"] for t in get_openai_tool_specs()],
    }


@app.get("/tools")
def tools() -> list[dict]:
    return get_openai_tool_specs()


@app.get("/models")
def models(refresh: bool = False) -> dict:
    """Models this endpoint offers, plus which one is the default."""
    settings = get_settings()
    try:
        available = models_registry.list_models(force_refresh=refresh)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502, detail=f"Could not list models: {exc}"
        ) from exc
    return {"default": settings.llm_model, "models": available}


def _resolve_model(requested: str | None) -> str:
    """Pick the model for a request, rejecting ids the endpoint doesn't offer."""
    settings = get_settings()
    if not requested:
        return settings.llm_model
    if not models_registry.is_known(requested):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{requested}'. See GET /models for the list.",
        )
    return requested


def _llm_error(exc: OpenAIError, model: str) -> HTTPException:
    """Turn a raw provider error into something the UI can show a user.

    Not every model behind an OpenAI-compatible proxy supports tool calling,
    and that failure is otherwise indistinguishable from a generic 500.
    """
    text = str(exc)
    lowered = text.lower()
    if any(k in lowered for k in ("tool", "function call")):
        return HTTPException(
            status_code=422,
            detail=(
                f"Model '{model}' could not complete a tool-calling request. "
                f"Try a different model. ({text[:200]})"
            ),
        )
    return HTTPException(status_code=502, detail=f"LLM call failed: {text[:300]}")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    model = _resolve_model(req.model)
    started = time.perf_counter()
    try:
        result = run_agent(req.message, system_prompt=req.system_prompt, model=model)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        raise _llm_error(exc, model) from exc
    latency_ms = int((time.perf_counter() - started) * 1000)

    usage.record(
        endpoint="/chat",
        model=result.model or model,
        prompt_tokens=result.usage.prompt_tokens,
        completion_tokens=result.usage.completion_tokens,
        total_tokens=result.usage.total_tokens,
        llm_calls=result.usage.llm_calls,
        latency_ms=latency_ms,
    )
    return result


@app.post("/extract", response_model=MeetingNotes)
def extract(req: ExtractRequest) -> MeetingNotes:
    model = _resolve_model(req.model)
    started = time.perf_counter()
    try:
        notes, tokens = extract_meeting_notes(req.text, model=model)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        raise _llm_error(exc, model) from exc
    latency_ms = int((time.perf_counter() - started) * 1000)

    usage.record(
        endpoint="/extract",
        model=model,
        prompt_tokens=tokens.prompt_tokens,
        completion_tokens=tokens.completion_tokens,
        total_tokens=tokens.total_tokens,
        llm_calls=tokens.llm_calls,
        latency_ms=latency_ms,
    )
    return notes


@app.post("/knowledge/seed")
def seed(req: SeedRequest) -> dict:
    store = get_vector_store()
    ids = store.add(req.documents)
    return {"added": len(ids), "ids": ids, "total": store.count()}


@app.post("/knowledge/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    store = get_vector_store()
    hits = store.search(req.query, top_k=req.top_k)
    return SearchResponse(query=req.query, hits=hits)


@app.get("/usage/summary", response_model=UsageSummary)
def usage_summary() -> UsageSummary:
    return usage.summary()


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")
