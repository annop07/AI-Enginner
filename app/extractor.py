"""Structured Output via Instructor.

Instructor patches the OpenAI client so that `response_model=<PydanticModel>`
forces the LLM's output to validate against that schema — with automatic
retries if the model returns something that doesn't fit. This is how you get
JSON you can trust 100%, instead of parsing free text and praying.
"""
from __future__ import annotations

import instructor

from openai import OpenAI

from app.config import get_settings
from app.schemas import MeetingNotes, TokenUsage


def _instructor_client() -> instructor.Instructor:
    settings = get_settings()
    if not settings.openai_configured:
        raise RuntimeError("OPENAI_API_KEY is not set. See .env.example.")
    base = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    # JSON mode asks the model to emit JSON matching our schema directly,
    # instead of relying on the tool-calling response format. This is the most
    # portable mode across OpenAI-compatible proxies (KKU, Gemini, Qwen, ...).
    return instructor.from_openai(base, mode=instructor.Mode.JSON)


def extract_meeting_notes(
    text: str, model: str | None = None
) -> tuple[MeetingNotes, TokenUsage]:
    """Return the validated model plus the tokens the extraction cost."""
    client = _instructor_client()
    settings = get_settings()
    # create_with_completion also hands back the raw completion, so we can
    # read its `usage` for the dashboard.
    notes, completion = client.chat.completions.create_with_completion(
        model=model or settings.llm_model,
        response_model=MeetingNotes,
        max_retries=2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract structured meeting notes from the user's text. "
                    "Identify participants and concrete action items with owners "
                    "and priorities. If a field is unknown, leave it null/empty."
                ),
            },
            {"role": "user", "content": text},
        ],
    )

    usage = TokenUsage()
    u = getattr(completion, "usage", None)
    if u:
        usage.add(u.prompt_tokens or 0, u.completion_tokens or 0, u.total_tokens or 0)
    return notes, usage
