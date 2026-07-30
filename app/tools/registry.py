"""A tiny, typed tool registry.

Each tool couples:
  - a Pydantic model describing its arguments (→ JSON Schema for the LLM), and
  - a Python callable that executes it.

The LLM sees the JSON Schema via OpenAI's `tools` parameter and picks which
tool to call. We validate its arguments against the Pydantic model before
running the callable, so a hallucinated argument shape fails loudly instead
of crashing the tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel, ValidationError


@dataclass
class Tool:
    name: str
    description: str
    args_model: Type[BaseModel]
    func: Callable[..., Any]

    def openai_spec(self) -> dict[str, Any]:
        """Render this tool as an OpenAI function-calling spec."""
        schema = self.args_model.model_json_schema()
        # OpenAI wants a plain object schema without $defs at the top for
        # simple tools; model_json_schema already gives a valid schema.
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    def run(self, raw_arguments: dict[str, Any]) -> Any:
        try:
            args = self.args_model.model_validate(raw_arguments)
        except ValidationError as exc:
            return {"error": "invalid_arguments", "detail": exc.errors()}
        return self.func(args)


REGISTRY: dict[str, Tool] = {}


def register(
    name: str, description: str, args_model: Type[BaseModel]
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a function as an agent tool."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        REGISTRY[name] = Tool(
            name=name, description=description, args_model=args_model, func=func
        )
        return func

    return decorator


def get_openai_tool_specs() -> list[dict[str, Any]]:
    return [tool.openai_spec() for tool in REGISTRY.values()]


def dispatch(name: str, raw_arguments: dict[str, Any]) -> Any:
    tool = REGISTRY.get(name)
    if tool is None:
        return {"error": "unknown_tool", "tool": name}
    return tool.run(raw_arguments)


# Import side-effect modules so their @register decorators run.
# (Placed at the bottom to avoid circular imports.)
from app.tools import builtins  # noqa: E402,F401
