"""Executor for standalone ASSERT / ASSERT_JSON steps against the last response."""

from __future__ import annotations

from testql.base import StepResult, StepStatus
from testql.ir import Step

from ..context import ExecutionContext
from .base import assemble_result, skipped_result, step_label


def _last_payload(ctx: ExecutionContext) -> dict:
    return {
        "status": ctx.last_status,
        "data": ctx.last_response,
        "headers": {},
    }


def execute(step: Step, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, step.name or "ASSERT_JSON")
    if ctx.last_response is None and ctx.last_status is None:
        return skipped_result(label, "no previous HTTP/API response")
    if not step.asserts:
        return StepResult(name=label, status=StepStatus.PASSED, message="no assertions")
    payload = _last_payload(ctx)
    return assemble_result(label, payload, step.asserts, ctx.dry_run)


__all__ = ["execute"]
