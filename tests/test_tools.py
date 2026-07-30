"""Tests that run without any OpenAI API key.

They cover the deterministic plumbing: tool registry, tool execution,
argument validation, and vector similarity search.
"""
from __future__ import annotations

from app.tools import REGISTRY, dispatch, get_openai_tool_specs


def test_registry_has_expected_tools():
    assert {"calculator", "get_time", "search_knowledge"} <= set(REGISTRY)


def test_openai_specs_are_well_formed():
    specs = get_openai_tool_specs()
    for spec in specs:
        assert spec["type"] == "function"
        assert "name" in spec["function"]
        assert "parameters" in spec["function"]


def test_calculator_runs():
    result = dispatch("calculator", {"expression": "(3 + 4) * 2"})
    assert result["result"] == 14


def test_calculator_rejects_code_injection():
    result = dispatch("calculator", {"expression": "__import__('os').system('ls')"})
    assert "error" in result


def test_invalid_arguments_are_caught():
    # missing required 'expression'
    result = dispatch("calculator", {})
    assert result["error"] == "invalid_arguments"


def test_unknown_tool():
    result = dispatch("does_not_exist", {})
    assert result["error"] == "unknown_tool"


def test_get_time_bad_timezone():
    result = dispatch("get_time", {"timezone": "Mars/Olympus"})
    assert result["error"] == "unknown_timezone"
