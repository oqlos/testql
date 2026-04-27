"""Data models for OQL/TQL to TestTOON converter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Row:
    """A row of values in a section."""
    values: dict[str, str]


@dataclass
class Section:
    """A section in the converted output."""
    type: str
    columns: list[str]
    rows: list[dict] = field(default_factory=list)
    comment: str = ""
