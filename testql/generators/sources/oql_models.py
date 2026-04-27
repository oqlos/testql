"""Data models for OQL/CQL scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OqlCommand:
    """Represents a single OQL/CQL command."""
    command: str
    target: str
    args: dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    line_number: int = 0


@dataclass
class ParsedScenario:
    """Represents a parsed OQL/CQL scenario file."""
    name: str
    source_file: Path
    config: dict[str, str] = field(default_factory=dict)
    setup_commands: list[OqlCommand] = field(default_factory=list)
    test_commands: list[OqlCommand] = field(default_factory=list)
    assertions: list[OqlCommand] = field(default_factory=list)
    cleanup_commands: list[OqlCommand] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
