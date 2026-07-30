"""The agent loop.

This is the core of the Week 1 deliverable: an LLM that, given a user
instruction and a set of tools, decides *on its own* which tools to call,
in what order, and when it has enough information to answer.

Flow (the classic tool-calling loop):
  1. Send conversation + tool specs to the LLM.
  2. If the LLM responds with tool_calls → run each tool, append the
     results to the conversation, and loop.
  3. If the LLM responds with content and no tool_calls → that's the answer.
  4. Stop after `max_tool_iterations` to guard against runaway loops.
"""
from __future__ import annotations

import json

from openai import OpenAI

from app.config import get_settings
from app.schemas import ChatResponse, TokenUsage, ToolCallTrace
from app.tools import dispatch, get_openai_tool_specs

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI agent. You have access to tools. "
    "Use them when they help answer the user accurately — for live data, "
    "calculations, or looking things up in the knowledge base. "
    "Do not guess when a tool can give you the real answer. "
    "When you have enough information, give a concise final answer."
)


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_configured:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file. "
            "See .env.example."
        )
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def run_agent(
    message: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> ChatResponse:
    settings = get_settings()
    client = _client()
    tools = get_openai_tool_specs()
    active_model = model or settings.llm_model

    messages: list[dict] = [
        {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    trace: list[ToolCallTrace] = []
    usage = TokenUsage()

    def _tally(resp) -> None:
        u = getattr(resp, "usage", None)
        if u:
            usage.add(
                u.prompt_tokens or 0,
                u.completion_tokens or 0,
                u.total_tokens or 0,
            )

    for iteration in range(1, settings.max_tool_iterations + 1):
        response = client.chat.completions.create(
            model=active_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        _tally(response)
        choice = response.choices[0].message

        # No tool calls → the model is done and this is the final answer.
        if not choice.tool_calls:
            return ChatResponse(
                answer=choice.content or "",
                tool_calls=trace,
                iterations=iteration,
                usage=usage,
                model=active_model,
            )

        # Record the assistant turn (with its tool call requests) verbatim.
        messages.append(
            {
                "role": "assistant",
                "content": choice.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in choice.tool_calls
                ],
            }
        )

        # Execute each requested tool and feed results back.
        for tc in choice.tool_calls:
            try:
                arguments = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = dispatch(tc.function.name, arguments)
            trace.append(
                ToolCallTrace(
                    tool=tc.function.name, arguments=arguments, result=result
                )
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                }
            )

    # Hit the iteration cap — ask for a best-effort answer without more tools.
    final = client.chat.completions.create(
        model=active_model,
        messages=messages
        + [
            {
                "role": "user",
                "content": "Stop calling tools and answer with what you have now.",
            }
        ],
    )
    _tally(final)
    return ChatResponse(
        answer=final.choices[0].message.content or "",
        tool_calls=trace,
        iterations=settings.max_tool_iterations,
        usage=usage,
        model=active_model,
    )
