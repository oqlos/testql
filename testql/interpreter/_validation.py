"""Validation mixin — text/NL validation of step outputs.

Adds a pluggable VALIDATE command that supports multiple validation
strategies (regex, contains, not_contains, template, semantic) over a
named target source (stdout / stderr / response / variable).

The semantic strategy does NOT run an LLM inline; it emits a structured
event ``nl_validate_request`` that an external evaluator (MCP tool /
service) can consume. This keeps the interpreter deterministic and
caches well in topology pipelines.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


def _resolve_target(interpreter: Any, target: str) -> str:
    """Resolve a target name to its current text value."""
    target = (target or "").strip().lower()
    shell_result = getattr(interpreter, "_last_shell_result", None) or {}

    if target in ("output", "stdout", "shell.stdout"):
        return str(shell_result.get("stdout", ""))
    if target in ("stderr", "shell.stderr"):
        return str(shell_result.get("stderr", ""))
    if target in ("exit_code", "returncode"):
        return str(shell_result.get("returncode", ""))
    if target in ("response", "api.response", "last_response"):
        return json.dumps(getattr(interpreter, "last_response", None) or {})
    # Variable lookup as a fallback (supports ${var} interpolation already
    # performed before _cmd_validate runs).
    val = interpreter.vars.get(target) if hasattr(interpreter, "vars") else None
    if val is None:
        return target  # treat as literal
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return str(val)


class ValidationMixin:
    """Mixin providing the VALIDATE command for textual / NL assertions."""

    def _cmd_validate(self, args: str, line: OqlLine) -> None:
        """VALIDATE <type> <target> "<criteria>"

        Types:
          - regex          → re.search(criteria, target_text)
          - contains       → criteria in target_text
          - not_contains   → criteria not in target_text
          - template       → criteria is path to file; whole file content
                             must appear (substring) in target_text
          - semantic       → emit ``nl_validate_request`` event for an
                             external LLM evaluator and PASS optimistically
                             (deterministic-first; opt-in evaluation runs
                             out-of-band).
        """
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.warn(
                f"L{line.number}: VALIDATE requires <type> <target> <criteria>"
            )
            return

        vtype, target, criteria = parts[0].lower(), parts[1], parts[2]
        criteria = criteria.strip().strip('"\'')
        text = _resolve_target(self, target)
        label = f"VALIDATE {vtype} {target}"

        if vtype == "regex":
            ok = bool(re.search(criteria, text, re.MULTILINE))
            self._record_validate(ok, label, criteria, text, line)
            return

        if vtype == "contains":
            ok = criteria in text
            self._record_validate(ok, label, criteria, text, line)
            return

        if vtype == "not_contains":
            ok = criteria not in text
            self._record_validate(ok, label, criteria, text, line)
            return

        if vtype == "template":
            tpl_path = Path(criteria)
            if not tpl_path.is_file():
                self.out.fail(f"{label}: template file not found: {criteria}")
                self.results.append(StepResult(
                    name=label, status=StepStatus.FAILED,
                    message=f"template file not found: {criteria}",
                ))
                return
            tpl = tpl_path.read_text(encoding="utf-8").strip()
            ok = tpl in text
            self._record_validate(ok, label, f"template:{criteria}", text, line)
            return

        if vtype == "semantic":
            event = {
                "type": "nl_validate_request",
                "target": target,
                "criteria": criteria,
                "text": text,
                "line": line.number,
            }
            if hasattr(self, "events") and isinstance(self.events, list):
                self.events.append(event)
            self.out.step(
                "🧠",
                f"{label} (semantic) → emitted nl_validate_request",
            )
            self.results.append(StepResult(
                name=label,
                status=StepStatus.PASSED,
                details={"semantic": True, "criteria": criteria},
            ))
            return

        self.out.warn(f"L{line.number}: Unknown VALIDATE type: {vtype}")
        self.results.append(StepResult(
            name=label, status=StepStatus.WARNING,
            message=f"unknown type: {vtype}",
        ))

    def _record_validate(
        self,
        ok: bool,
        label: str,
        criteria: str,
        text: str,
        line: OqlLine,
    ) -> None:
        snippet = text[:120].replace("\n", " ")
        if ok:
            self.out.step("  ✅", f"{label} :: {criteria}")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{label} :: {criteria} (text: {snippet!r})")
            self.errors.append(
                f"L{line.number}: {label} failed for criteria {criteria!r}"
            )
            self.results.append(StepResult(
                name=label, status=StepStatus.FAILED,
                message=f"criteria {criteria!r} did not match",
            ))
