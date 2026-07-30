"""Built-in tools available to the agent.

Three flavours on purpose, to show the range of what tool-calling covers:
  - calculator : pure local computation
  - get_time   : reads live state the LLM cannot know
  - search_knowledge : hits the vector DB (Retrieval-Augmented tool call)
"""
from __future__ import annotations

import ast
import datetime as dt
import operator as op
import zoneinfo

from pydantic import BaseModel, Field

from app.tools.registry import register
from app.vectorstore import get_vector_store

# --------------------------------------------------------------------------- #
# calculator — safe arithmetic (no eval())
# --------------------------------------------------------------------------- #

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


class CalculatorArgs(BaseModel):
    expression: str = Field(..., description="Arithmetic expression, e.g. '(3 + 4) * 2'")


@register(
    name="calculator",
    description="Evaluate a basic arithmetic expression (+ - * / ** %).",
    args_model=CalculatorArgs,
)
def calculator(args: CalculatorArgs) -> dict:
    try:
        value = _safe_eval(ast.parse(args.expression, mode="eval").body)
        return {"expression": args.expression, "result": value}
    except Exception as exc:  # noqa: BLE001
        return {"error": "could_not_evaluate", "detail": str(exc)}


# --------------------------------------------------------------------------- #
# get_time — live state
# --------------------------------------------------------------------------- #


class TimeArgs(BaseModel):
    timezone: str = Field(
        "UTC", description="IANA timezone name, e.g. 'Asia/Bangkok' or 'UTC'"
    )


@register(
    name="get_time",
    description="Get the current date and time in a given IANA timezone.",
    args_model=TimeArgs,
)
def get_time(args: TimeArgs) -> dict:
    try:
        tz = zoneinfo.ZoneInfo(args.timezone)
    except Exception:
        return {"error": "unknown_timezone", "timezone": args.timezone}
    now = dt.datetime.now(tz)
    return {
        "timezone": args.timezone,
        "iso": now.isoformat(),
        "human": now.strftime("%A, %d %B %Y %H:%M:%S"),
    }


# --------------------------------------------------------------------------- #
# search_knowledge — RAG-style tool over the vector DB
# --------------------------------------------------------------------------- #


class KnowledgeArgs(BaseModel):
    query: str = Field(..., description="What to look up in the knowledge base")
    top_k: int = Field(3, ge=1, le=10)


@register(
    name="search_knowledge",
    description=(
        "Search the internal knowledge base for relevant facts. "
        "Use this whenever the user asks about domain-specific information "
        "that may have been stored earlier."
    ),
    args_model=KnowledgeArgs,
)
def search_knowledge(args: KnowledgeArgs) -> dict:
    store = get_vector_store()
    hits = store.search(args.query, top_k=args.top_k)
    return {
        "query": args.query,
        "hits": [{"text": h.text, "score": h.score, "metadata": h.metadata} for h in hits],
    }
