"""Echo command - Generate AI-friendly project context from toon + doql.

Usage:
    from testql.commands.echo import echo, generate_context, format_text_output
    
    context = generate_context(Path("./my-project"))
    print(format_text_output(context))
"""

from .parsers.doql import parse_doql_less
from .parsers.toon import parse_toon_scenarios
from .context import generate_context
from .formatters.text import format_text_output
from .cli import echo

__all__ = [
    "parse_doql_less",
    "parse_toon_scenarios",
    "generate_context",
    "format_text_output",
    "echo",
]
