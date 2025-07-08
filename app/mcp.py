"""Simple Model Context Protocol utilities."""

"""Utilities for the Model Context Protocol (MCP)."""

from typing import Iterable, Callable, Dict, List
import json
from langchain.schema import ToolMessage


def _uppercase(text: str) -> str:
    return text.upper()


def _excited(text: str) -> str:
    return text + "!"


# Available MCP tool functions
TOOLS: Dict[str, Callable[[str], str]] = {
    "uppercase": _uppercase,
    "excited": _excited,
}

# OpenAI tool schema definitions for each MCP tool
TOOL_SCHEMAS: Dict[str, dict] = {
    "uppercase": {
        "type": "function",
        "function": {
            "name": "uppercase",
            "description": "Return text in upper case",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    "excited": {
        "type": "function",
        "function": {
            "name": "excited",
            "description": "Append an exclamation mark to text",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
}


def apply_mcp(text: str, tool_names: Iterable[str]) -> str:
    """Apply MCP tools in order provided."""
    for name in tool_names:
        func = TOOLS.get(name)
        if func:
            text = func(text)
    return text


def handle_tool_calls(tool_calls: List[dict]) -> List[ToolMessage]:
    """Execute tool calls from OpenAI and return ToolMessage objects."""
    messages = []
    for call in tool_calls:
        name = call.get("function", {}).get("name")
        args_json = call.get("function", {}).get("arguments", "{}")
        try:
            args = json.loads(args_json)
        except Exception:  # pragma: no cover - invalid JSON
            args = {}
        func = TOOLS.get(name)
        if func:
            result = func(args.get("text", ""))
            messages.append(ToolMessage(content=result, tool_call_id=call.get("id", "")))
    return messages
