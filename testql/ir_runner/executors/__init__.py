"""Executor registry — maps each `Step.kind` to a callable.

Adding a new step kind:

  1. Implement `execute(step, ctx) -> StepResult` in a new module.
  2. Add the entry below.
"""

from __future__ import annotations

from typing import Callable

from testql.base import StepResult
from testql.ir import Step

from ..context import ExecutionContext
from . import api, encoder, gui, graphql, nl, proto, shell, sql, unit
from .base import StepExecutor, error_result, step_label


_REGISTRY: dict[str, Callable[[Step, ExecutionContext], StepResult]] = {
    "api": api.execute,
    "sql": sql.execute,
    "proto": proto.execute,
    "graphql": graphql.execute,
    "shell": shell.execute,
    "encoder": encoder.execute,
    "unit": unit.execute,
    "nl": nl.execute,
    "gui": gui.execute,
}


def get_executor(kind: str) -> Callable[[Step, ExecutionContext], StepResult] | None:
    """Return the executor for `kind`, or None if not registered."""
    return _REGISTRY.get(kind)


def register(kind: str, executor: Callable[[Step, ExecutionContext], StepResult]) -> None:
    """Register a custom executor (e.g. for an external step kind)."""
    _REGISTRY[kind] = executor


def supported_kinds() -> list[str]:
    return sorted(_REGISTRY.keys())


__all__ = [
    "StepExecutor", "get_executor", "register", "supported_kinds",
    "error_result", "step_label",
]
