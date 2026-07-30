"""Pydantic schemas — the contract between the API, the LLM, and tools.

These models power three things:
  1. Request/response validation for the HTTP API.
  2. Structured Output extraction via Instructor (see routers/extract).
  3. The trace of tool calls returned by the agent.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Chat / agent
# --------------------------------------------------------------------------- #


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User instruction to the agent")
    system_prompt: str | None = Field(
        default=None, description="Optional override for the system prompt"
    )
    model: str | None = Field(
        default=None,
        description="Model id to use for this request. Falls back to LLM_MODEL.",
    )


class ToolCallTrace(BaseModel):
    """A record of one tool the agent chose to invoke."""

    tool: str
    arguments: dict[str, Any]
    result: Any


class TokenUsage(BaseModel):
    """Token accounting for one API request (summed over all LLM calls it made)."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = Field(0, description="Number of LLM round-trips this request made")

    def add(self, prompt: int, completion: int, total: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total
        self.llm_calls += 1


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    iterations: int = Field(..., description="How many LLM turns the agent used")
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = Field("", description="Model that actually answered")


# --------------------------------------------------------------------------- #
# Structured Output (Instructor) — a worked example schema
# --------------------------------------------------------------------------- #


class ActionItem(BaseModel):
    """One extracted task from free-form text."""

    title: str = Field(..., description="Short imperative description of the task")
    owner: str | None = Field(None, description="Person responsible, if named")
    priority: Literal["low", "medium", "high"] = Field(
        "medium", description="Inferred urgency of the task"
    )
    due: str | None = Field(None, description="Due date/time in natural language, if any")


class MeetingNotes(BaseModel):
    """Structured summary extracted from meeting notes / an email."""

    summary: str = Field(..., description="One or two sentence summary")
    participants: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1)
    model: str | None = Field(
        default=None,
        description="Model id to use for this request. Falls back to LLM_MODEL.",
    )


# --------------------------------------------------------------------------- #
# Knowledge base / vector search
# --------------------------------------------------------------------------- #


class Document(BaseModel):
    id: str | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SeedRequest(BaseModel):
    documents: list[Document]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)


class SearchHit(BaseModel):
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


# --------------------------------------------------------------------------- #
# Usage dashboard
# --------------------------------------------------------------------------- #


class UsageEvent(BaseModel):
    id: int
    ts: str
    endpoint: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int
    latency_ms: int


class ModelUsage(BaseModel):
    model: str
    requests: int
    total_tokens: int


class EndpointUsage(BaseModel):
    endpoint: str
    requests: int
    total_tokens: int


class TimePoint(BaseModel):
    bucket: str  # ISO date/hour
    total_tokens: int
    requests: int


class UsageSummary(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    avg_latency_ms: float
    by_model: list[ModelUsage]
    by_endpoint: list[EndpointUsage]
    timeseries: list[TimePoint]
    recent: list[UsageEvent]
