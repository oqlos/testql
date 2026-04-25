"""IRRunner — execute a `TestPlan` end-to-end.

Walks every step in order, dispatches via the executor registry, accumulates
`StepResult`s into a `ScriptResult`. Exceptions raised inside an executor are
caught and recorded as ERROR; they do not abort the run.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Union

from testql.adapters.registry import get_registry
from testql.base import ScriptResult, StepResult, StepStatus, VariableStore
from testql.ir import TestPlan

from .assertion_eval import navigate
from .context import ExecutionContext
from .executors import error_result, get_executor, step_label


# ── Plan loading ────────────────────────────────────────────────────────────


def load_plan(source: Union[str, Path, TestPlan]) -> TestPlan:
    """Load a TestPlan from a file path, raw source, or pass through if already IR."""
    if isinstance(source, TestPlan):
        return source
    if not isinstance(source, (str, Path)):
        raise ValueError(f"unsupported source type: {type(source).__name__}")
    import testql.adapters  # noqa: F401
    adapter = get_registry().detect(source)
    if adapter is None:
        raise ValueError(f"no adapter detected for source: {source!r}")
    return adapter.parse(source)


# ── Run a single step ───────────────────────────────────────────────────────


def _apply_captures(step, result: StepResult, ctx: ExecutionContext) -> None:
    """Walk `step.captures`; resolve each `from_path` against the step's payload
    and store the value into `ctx.vars`. Missing paths emit a warning but do
    not fail the step.
    """
    captures = getattr(step, "captures", None) or []
    if not captures:
        return
    payload = (result.details or {}).get("payload", {})
    for capture in captures:
        value = navigate(payload, capture.from_path)
        if value is None:
            ctx.warnings.append(
                f"capture {capture.var_name!r} from {capture.from_path!r}: path not found"
            )
            continue
        ctx.vars.set(capture.var_name, value)


def _run_step(step, ctx: ExecutionContext) -> StepResult:
    executor = get_executor(step.kind)
    if executor is None:
        return error_result(step_label(step, step.kind.upper()),
                            ValueError(f"no executor for kind: {step.kind!r}"))
    t0 = time.monotonic()
    try:
        result = executor(step, ctx)
    except Exception as e:
        return error_result(step_label(step, step.kind.upper()), e)
    result.duration_ms = (time.monotonic() - t0) * 1000
    if result.status not in (StepStatus.ERROR, StepStatus.SKIPPED):
        _apply_captures(step, result, ctx)
    return result


# ── Public Runner ───────────────────────────────────────────────────────────


class IRRunner:
    """Execute a `TestPlan` step-by-step against an `ExecutionContext`."""

    def __init__(self, *, api_url: str = "http://localhost:8101",
                 encoder_url: str = "http://localhost:8105",
                 graphql_url: str = "http://localhost:8101/graphql",
                 dry_run: bool = False, quiet: bool = True,
                 variables: Optional[dict] = None) -> None:
        self.ctx = ExecutionContext(
            vars=VariableStore(variables or {}),
            api_url=api_url, encoder_url=encoder_url,
            graphql_url=graphql_url, dry_run=dry_run,
        )
        self.ctx.out.quiet = quiet

    def _apply_plan_config(self, plan: TestPlan) -> None:
        for key, value in plan.config.items():
            if not self.ctx.vars.has(key):
                self.ctx.vars.set(key, value)
        api_base = plan.config.get("api.base_url") or plan.config.get("base_url")
        encoder_base = plan.config.get("encoder.base_url") or plan.config.get("encoder_url")
        graphql_base = plan.config.get("graphql.url") or plan.config.get("graphql_url")
        if api_base:
            self.ctx.api_url = str(api_base).rstrip("/")
        if encoder_base:
            self.ctx.encoder_url = str(encoder_base).rstrip("/")
        if graphql_base:
            self.ctx.graphql_url = str(graphql_base)

    def run(self, plan: Union[str, Path, TestPlan],
            source_label: str = "<plan>") -> ScriptResult:
        """Execute `plan`. Returns a `ScriptResult` with all step outcomes."""
        loaded = load_plan(plan)
        self._apply_plan_config(loaded)
        t0 = time.monotonic()
        for step in loaded.steps:
            result = _run_step(step, self.ctx)
            self.ctx.results.append(result)
            if result.status in (StepStatus.FAILED, StepStatus.ERROR):
                self.ctx.errors.append(f"{result.name}: {result.message}")
        elapsed = (time.monotonic() - t0) * 1000
        ok = all(r.status in (StepStatus.PASSED, StepStatus.SKIPPED)
                 for r in self.ctx.results)
        label = loaded.metadata.name or source_label
        return ScriptResult(
            source=label, ok=ok, steps=self.ctx.results,
            variables=self.ctx.vars.all(), errors=self.ctx.errors,
            warnings=self.ctx.warnings, duration_ms=elapsed,
        )


def run_plan(plan: Union[str, Path, TestPlan], **kwargs) -> ScriptResult:
    """Convenience: build a runner and execute `plan` in one call."""
    return IRRunner(**kwargs).run(plan)


__all__ = ["IRRunner", "run_plan", "load_plan"]
