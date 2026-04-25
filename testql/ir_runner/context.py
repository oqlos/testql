"""Execution context shared across all step executors.

Encapsulates the bits of state every executor needs (variables, output sink,
result accumulator, dry-run flag, default URLs) without forcing them to inherit
a deep mixin chain like the legacy interpreter does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testql.base import InterpreterOutput, StepResult, VariableStore


@dataclass
class ExecutionContext:
    """State container threaded through every executor call."""

    vars: VariableStore = field(default_factory=VariableStore)
    out: InterpreterOutput = field(default_factory=InterpreterOutput)
    results: list[StepResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Defaults / configuration
    api_url: str = "http://localhost:8101"
    encoder_url: str = "http://localhost:8105"
    graphql_url: str = "http://localhost:8101/graphql"
    dry_run: bool = False

    # Last-response state (for backwards-compatible assertions on `status`,
    # `data.*`, `rowcount`, etc., which reference the *current* step's result).
    last_response: Any = None
    last_status: int | None = None

    def record(self, result: StepResult) -> None:
        """Append a step result and emit a one-line summary."""
        self.results.append(result)


__all__ = ["ExecutionContext"]
