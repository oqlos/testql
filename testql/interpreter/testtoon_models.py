"""Data models for TestTOON parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToonSection:
    """Represents a section in TestTOON format."""
    type: str
    columns: list[str]
    rows: list[dict]
    expected_count: Optional[int] = None
    is_mapping: bool = False  # True if using YAML mapping format instead of tabular

    def validate(self) -> list[str]:
        """Validate section against expected row count."""
        errors = []
        if self.expected_count is not None and len(self.rows) != self.expected_count:
            errors.append(
                f"{self.type}[{self.expected_count}]: "
                f"declared {self.expected_count}, found {len(self.rows)}"
            )
        return errors


@dataclass
class ToonScript:
    """Represents a parsed TestTOON script."""
    meta: dict[str, str] = field(default_factory=dict)
    sections: list[ToonSection] = field(default_factory=list)
