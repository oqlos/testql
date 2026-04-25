"""Executor for `NlStep` — best-effort delegation to the NL adapter.

The IR runner cannot execute raw natural-language; it only flags the step as
SKIPPED with a guidance message. To execute NL plans, re-render them through
the NL adapter into typed steps first (e.g. via `testql generate-ir`).
"""

from __future__ import annotations

from testql.base import StepResult
from testql.ir import NlStep

from ..context import ExecutionContext
from .base import skipped_result, step_label


def execute(step: NlStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "NL")
    return skipped_result(
        label, "NL steps must be resolved to typed IR first (run through NLDSLAdapter)",
    )


__all__ = ["execute"]
