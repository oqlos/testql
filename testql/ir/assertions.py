"""Assertion node for the Unified IR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Assertion:
    """Single assertion against a step's outcome.

    Attributes:
        field: Path/name of the value being checked (e.g. "status", "data.user.id").
        op: Comparison operator (e.g. "==", "!=", "contains", ">", "<", ">=", "<=", "matches").
        expected: Expected value (any literal).
        actual_path: Optional alternative source path (for nested data extraction).
        message: Optional human-readable label.
    """

    field: str
    op: str = "=="
    expected: Any = None
    actual_path: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> dict:
        out: dict = {"field": self.field, "op": self.op, "expected": self.expected}
        if self.actual_path is not None:
            out["actual_path"] = self.actual_path
        if self.message is not None:
            out["message"] = self.message
        return out
