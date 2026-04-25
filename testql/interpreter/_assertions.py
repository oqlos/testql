"""Assertions mixin for IqlInterpreter."""

from __future__ import annotations

from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import IqlLine
from ._api_runner import _navigate_json_path


_COMPARE_OPS: dict[str, Any] = {
    "==": lambda a, b: a == b,
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: (a or 0) > b,
    ">=": lambda a, b: (a or 0) >= b,
    "<":  lambda a, b: (a or 0) < b,
    "<=": lambda a, b: (a or 0) <= b,
}


class AssertionsMixin:
    """Mixin providing ASSERT_STATUS, ASSERT_OK, ASSERT_CONTAINS, ASSERT_JSON."""

    def _cmd_assert_status(self, args: str, line: IqlLine) -> None:
        """ASSERT_STATUS <code> — check last HTTP status code."""
        expected = int(args.strip())
        ok = self.last_status == expected
        name = f"ASSERT_STATUS {expected}"
        if ok:
            self.out.step("  ✅", name)
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} (got {self.last_status})")
            self.errors.append(f"L{line.number}: expected status {expected}, got {self.last_status}")
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f"expected {expected}, got {self.last_status}",
            ))

    def _cmd_assert_ok(self, args: str, line: IqlLine) -> None:
        """ASSERT_OK — check last status was 2xx."""
        ok = 200 <= self.last_status < 300
        name = "ASSERT_OK"
        if ok:
            self.out.step("  ✅", f"{name} (status {self.last_status})")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} (status {self.last_status})")
            self.errors.append(f"L{line.number}: expected 2xx, got {self.last_status}")
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f"status {self.last_status}",
            ))

    def _cmd_assert_contains(self, args: str, line: IqlLine) -> None:
        """ASSERT_CONTAINS "needle" — check needle present in JSON-serialised response."""
        import json as _json
        needle = args.strip().strip("\"'")
        haystack = _json.dumps(self.last_response or {})
        ok = needle in haystack
        name = f'ASSERT_CONTAINS "{needle}"'
        if ok:
            self.out.step("  ✅", name)
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} — not found")
            self.errors.append(f'L{line.number}: "{needle}" not found in response')
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f'"{needle}" not found',
            ))

    def _cmd_assert_json(self, args: str, line: IqlLine) -> None:
        """ASSERT_JSON path op value — e.g. ASSERT_JSON data.length > 0"""
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.warn(f"L{line.number}: ASSERT_JSON requires <path> <op> <value>")
            return

        path, op, expected_str = parts[0], parts[1], parts[2]
        obj = _navigate_json_path(self.last_response, path)

        # Handle None values - fail assertion if path not found
        if obj is None:
            desc = f"ASSERT_JSON {path} {op} {expected_str}"
            self.out.step("  ❌", f"{desc} (path not found)")
            self.errors.append(f"L{line.number}: {desc} failed (path '{path}' not found in response)")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"path '{path}' not found",
            ))
            return

        try:
            expected: Any = float(expected_str) if "." in expected_str else int(expected_str)
        except ValueError:
            expected = expected_str.strip("\"'")

        cmp_fn = _COMPARE_OPS.get(op)
        ok = cmp_fn(obj, expected) if cmp_fn else False
        desc = f"ASSERT_JSON {path} {op} {expected_str}"

        if ok:
            self.out.step("  ✅", f"{desc} (actual: {obj})")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{desc} (actual: {obj})")
            self.errors.append(f"L{line.number}: {desc} failed (actual: {obj})")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"actual: {obj}",
            ))
