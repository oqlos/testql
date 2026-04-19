"""Output formatters for echo command.

- text: Human-readable text output
- json: JSON output (handled directly in CLI)
"""

from .text import format_text_output

__all__ = ["format_text_output"]
