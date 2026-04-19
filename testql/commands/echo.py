"""Echo command - Generate AI-friendly project context from toon + doql.

This is a backward-compatible re-export. New code should use:
    from testql.commands.echo import echo, generate_context, format_text_output
"""

from __future__ import annotations

# Re-export from new structured package
from .echo import (
    parse_doql_less,
    parse_toon_scenarios,
    generate_context,
    format_text_output,
    echo,
)

__all__ = [
    "parse_doql_less",
    "parse_toon_scenarios",
    "generate_context",
    "format_text_output",
    "echo",
]
