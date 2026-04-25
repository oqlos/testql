"""Executor protocol and shared helpers."""

from __future__ import annotations

from typing import Callable, Protocol

from testql.base import StepResult, StepStatus
from testql.ir import Step

from ..assertion_eval import AssertionResult, evaluate_all
from ..context import ExecutionContext


class StepExecutor(Protocol):
    """Callable contract every executor must satisfy."""

    def __call__(self, step: Step, ctx: ExecutionContext) -> StepResult: ...


# ── Shared helpers ─────────────────────────────────────────────────────────


def step_label(step: Step, prefix: str) -> str:
    """A short, human-readable label for a step result line."""
    return step.name or f"{prefix} {step.kind}"


def _aggregate_assertion_status(passed: bool, dry_run: bool) -> StepStatus:
    if dry_run:
        return StepStatus.PASSED
    return StepStatus.PASSED if passed else StepStatus.FAILED


def _compose_message(base: str, failed_msgs: list[str]) -> str:
    if not failed_msgs:
        return base
    joined = "; ".join(failed_msgs)
    return joined if not base else f"{base} | {joined}"


def assemble_result(
    name: str, payload: dict, assertions: list,
    dry_run: bool, base_message: str = "",
) -> StepResult:
    """Run assertions against `payload`, build a `StepResult`."""
    a_results: list[AssertionResult] = evaluate_all(assertions, payload)
    all_passed = all(r.passed for r in a_results)
    status = _aggregate_assertion_status(all_passed, dry_run)
    failed_msgs = [r.message for r in a_results if not r.passed]
    return StepResult(
        name=name, status=status,
        message=_compose_message(base_message, failed_msgs),
        details={"payload": payload, "assertions": [r.to_dict() for r in a_results]},
    )


def error_result(name: str, exc: Exception) -> StepResult:
    return StepResult(name=name, status=StepStatus.ERROR, message=str(exc))


def skipped_result(name: str, reason: str) -> StepResult:
    return StepResult(name=name, status=StepStatus.SKIPPED, message=reason)


__all__ = [
    "StepExecutor", "step_label",
    "assemble_result", "error_result", "skipped_result",
]
