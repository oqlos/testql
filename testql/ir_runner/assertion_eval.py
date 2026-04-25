"""Generic assertion evaluation for IR `Assertion`s.

Each `Assertion` references a dotted `field` path (e.g. `status`, `data.0.id`,
`rowcount`) inside the per-step *response payload* assembled by an executor.
This module handles:

  * dotted-path navigation through dicts, lists and dataclass-like objects
  * the operator table (`==`, `!=`, `<`, `>`, `<=`, `>=`, `contains`, `matches`,
    `in`, `not in`)
  * a typed `AssertionResult` with `passed/actual/message` for reporting
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from testql.ir import Assertion


# ── Path navigation ─────────────────────────────────────────────────────────


def _next_segment(current: Any, segment: str) -> Any:
    if current is None:
        return None
    if isinstance(current, dict):
        return current.get(segment)
    if isinstance(current, list) and segment.isdigit():
        idx = int(segment)
        return current[idx] if 0 <= idx < len(current) else None
    return getattr(current, segment, None)


def navigate(payload: Any, path: str) -> Any:
    """Resolve a dotted `path` inside `payload`. Empty `path` returns the payload."""
    if not path:
        return payload
    current = payload
    for segment in path.split("."):
        current = _next_segment(current, segment)
    return current


# ── Operator table ──────────────────────────────────────────────────────────


def _op_contains(actual: Any, expected: Any) -> bool:
    if actual is None:
        return False
    return expected in actual


def _op_matches(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return False
    return re.search(str(expected), str(actual)) is not None


_OPS: dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda a, b: a == b,
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<":  lambda a, b: a is not None and a < b,
    "<=": lambda a, b: a is not None and a <= b,
    ">":  lambda a, b: a is not None and a > b,
    ">=": lambda a, b: a is not None and a >= b,
    "contains": _op_contains,
    "matches":  _op_matches,
    "in":       lambda a, b: a in (b or []),
    "not in":   lambda a, b: a not in (b or []),
}


# ── Public API ──────────────────────────────────────────────────────────────


@dataclass
class AssertionResult:
    passed: bool
    actual: Any
    expected: Any
    op: str
    field: str
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "field": self.field,
            "op": self.op,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
        }


def evaluate(assertion: Assertion, payload: Any) -> AssertionResult:
    """Evaluate `assertion` against `payload` and return a structured result."""
    actual = navigate(payload, assertion.field)
    op_fn = _OPS.get(assertion.op)
    if op_fn is None:
        return AssertionResult(
            passed=False, actual=actual, expected=assertion.expected,
            op=assertion.op, field=assertion.field,
            message=f"unknown operator: {assertion.op!r}",
        )
    passed = bool(op_fn(actual, assertion.expected))
    msg = "" if passed else (
        f"expected {assertion.field} {assertion.op} {assertion.expected!r}, got {actual!r}"
    )
    return AssertionResult(
        passed=passed, actual=actual, expected=assertion.expected,
        op=assertion.op, field=assertion.field, message=msg,
    )


def evaluate_all(assertions: list[Assertion], payload: Any) -> list[AssertionResult]:
    """Evaluate every assertion in order. Empty list ⇒ empty result list."""
    return [evaluate(a, payload) for a in assertions]


__all__ = ["AssertionResult", "evaluate", "evaluate_all", "navigate"]
