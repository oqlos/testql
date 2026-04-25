"""Executor for `UnitStep` — invoke pytest on a target node-id."""

from __future__ import annotations

import subprocess
import sys

from testql.base import StepResult, StepStatus
from testql.ir import UnitStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import error_result, step_label


def _payload(returncode: int, stdout: str, stderr: str) -> dict:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr,
            "passed": returncode == 0}


def execute(step: UnitStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "UNIT")
    target = interp_value(step.target, ctx.vars)
    if not target:
        return error_result(label, ValueError("UnitStep.target is empty"))
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "target": target})
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", target, "-q"],
                              capture_output=True, text=True, timeout=300)
    except Exception as e:
        return error_result(label, e)
    payload = _payload(proc.returncode, proc.stdout, proc.stderr)
    ctx.last_response = payload
    status = StepStatus.PASSED if proc.returncode == 0 else StepStatus.FAILED
    return StepResult(name=label, status=status,
                      message=proc.stderr.strip().split("\n")[-1] if proc.returncode else "",
                      details=payload)


__all__ = ["execute"]
