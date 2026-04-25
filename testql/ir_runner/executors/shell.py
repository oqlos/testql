"""Executor for `ShellStep` — subprocess execution + exit-code assertion."""

from __future__ import annotations

import subprocess

from testql.base import StepResult, StepStatus
from testql.ir import ShellStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


def _aggregate_status(returncode: int, expect_exit_code: int | None) -> StepStatus:
    if expect_exit_code is not None:
        return StepStatus.PASSED if returncode == expect_exit_code else StepStatus.FAILED
    return StepStatus.PASSED if returncode == 0 else StepStatus.WARNING


def _payload(returncode: int, stdout: str, stderr: str) -> dict:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


def execute(step: ShellStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "SHELL")
    command = interp_value(step.command, ctx.vars)
    cwd = interp_value(step.cwd, ctx.vars) if step.cwd else None
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "command": command})
    try:
        proc = subprocess.run(command, shell=True, capture_output=True,
                              text=True, timeout=60, cwd=cwd)
    except Exception as e:
        return error_result(label, e)
    payload = _payload(proc.returncode, proc.stdout, proc.stderr)
    ctx.last_response = payload
    result = assemble_result(label, payload, step.asserts, ctx.dry_run)
    # If no assertions, fall back to expect_exit_code or zero-exit convention.
    if not step.asserts:
        result.status = _aggregate_status(proc.returncode, step.expect_exit_code)
    return result


__all__ = ["execute"]
