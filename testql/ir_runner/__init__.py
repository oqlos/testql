"""testql.ir_runner — Execute Unified IR `TestPlan`s.

Sits next to the legacy `testql.interpreter` package without replacing it.
Where the legacy interpreter consumes line-based `OqlScript` and emits events,
this runner walks typed `TestPlan` steps and dispatches them to per-kind
executors with no mixin chains.

Entry-points:

    from testql.ir_runner import IRRunner, run_plan

    # Single-shot:
    result = run_plan("scenario.testql.toon.yaml")

    # Reusable (variables shared across calls):
    runner = IRRunner(api_url="http://localhost:8000", dry_run=False)
    result = runner.run(plan_or_path)
"""

from __future__ import annotations

from .assertion_eval import AssertionResult, evaluate, evaluate_all, navigate
from .context import ExecutionContext
from .engine import IRRunner, load_plan, run_plan
from .executors import get_executor, register, supported_kinds
from .interpolation import interp_value

__all__ = [
    "IRRunner", "run_plan", "load_plan",
    "ExecutionContext",
    "AssertionResult", "evaluate", "evaluate_all", "navigate",
    "interp_value",
    "get_executor", "register", "supported_kinds",
]
