"""Executor for `GuiStep` — emit-only stub.

Real browser execution lives in the legacy interpreter behind an optional
Playwright dependency. The IR runner records GuiSteps as SKIPPED so a plan
mixing GUI + API + SQL still reports the non-GUI portions accurately.
"""

from __future__ import annotations

from testql.base import StepResult, StepStatus
from testql.ir import GuiStep

from ..context import ExecutionContext
from .base import step_label


def execute(step: GuiStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, f"GUI:{step.action}")
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "action": step.action})
    return StepResult(
        name=label, status=StepStatus.SKIPPED,
        message="GUI steps require Playwright; use legacy `testql run`",
        details={"action": step.action, "selector": step.selector,
                 "path": step.path, "value": step.value},
    )


__all__ = ["execute"]
