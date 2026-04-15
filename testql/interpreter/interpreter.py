"""
testql.interpreter.interpreter
— IQL / TestQL interpreter (refactored into subpackage).

Import path unchanged: `from testql.interpreter import IqlInterpreter`
"""

from __future__ import annotations

import time
from typing import Any

from testql.base import BaseInterpreter, ScriptResult, StepResult, StepStatus

from ._parser import IqlLine, IqlScript, parse_iql
from ._api_runner import ApiRunnerMixin
from ._assertions import AssertionsMixin
from ._encoder import EncoderMixin
from ._flow import FlowMixin

from ._websockets import WebSocketMixin


class IqlInterpreter(ApiRunnerMixin, AssertionsMixin, EncoderMixin, FlowMixin, WebSocketMixin, BaseInterpreter):
    """
    IQL interpreter — runs .iql / .tql scripts.

    Features:
      - SET/GET variables with ${var} interpolation
      - API calls (GET/POST/PUT/DELETE) with response capture
      - CAPTURE var FROM "json.path" — response chaining
      - ASSERT_STATUS, ASSERT_CONTAINS, ASSERT_JSON assertions
      - INCLUDE to compose scripts
      - NAVIGATE, CLICK, INPUT, SELECT_DEVICE, etc. (emit events)
      - Encoder HW commands (ENCODER_ON/OFF/SCROLL/CLICK/…)
      - WAIT, LOG, EMIT
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8101",
        variables: dict[str, Any] | None = None,
        quiet: bool = False,
        dry_run: bool = False,
        include_paths: list[str] | None = None,
        bridge_url: str | None = None,
    ):
        super().__init__(variables=variables, quiet=quiet, bridge_url=bridge_url)
        self.api_url = api_url
        self.dry_run = dry_run
        self.include_paths = include_paths or ["."]
        self.last_response: dict[str, Any] | None = None
        self.last_status: int = 0
        self.events: list[dict[str, Any]] = []
        self._included: set[str] = set()  # prevent circular includes

    def parse(self, source: str, filename: str = "<string>") -> IqlScript:
        return parse_iql(source, filename)

    def execute(self, parsed: IqlScript) -> ScriptResult:
        t0 = time.monotonic()
        self.out.step("📜", f"IQL: {parsed.filename}")

        for line in parsed.lines:
            args = self.vars.interpolate(line.args)
            try:
                self._dispatch(line.command, args, line)
            except Exception as e:
                self.errors.append(f"L{line.number}: {e}")
                self.out.fail(f"L{line.number}: {e}")
                self.results.append(StepResult(
                    name=line.raw, status=StepStatus.ERROR, message=str(e),
                ))

        elapsed = (time.monotonic() - t0) * 1000
        ok = all(r.status in (StepStatus.PASSED, StepStatus.SKIPPED) for r in self.results)
        sr = ScriptResult(
            source=parsed.filename, ok=ok, steps=self.results,
            variables=self.vars.all(), errors=self.errors,
            warnings=self.warnings, duration_ms=elapsed,
        )
        self.out.emit("")
        self.out.emit(sr.summary())
        return sr

    # ── Command dispatch ──────────────────────────────────────────────────────

    def _dispatch(self, cmd: str, args: str, line: IqlLine) -> None:
        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler:
            handler(args, line)
        else:
            self._emit_event(cmd.lower(), args, line)

    # ── Variables ─────────────────────────────────────────────────────────────

    def _cmd_set(self, args: str, line: IqlLine) -> None:
        parts = args.split(None, 1)
        if len(parts) < 2:
            self.out.warn(f"L{line.number}: SET requires <name> <value>")
            return
        key, val = parts[0], parts[1].strip().strip('"\'')
        self.vars.set(key, val)
        self.out.step("📝", f"SET {key} = {val}")

    def _cmd_get(self, args: str, line: IqlLine) -> None:
        key = args.strip()
        val = self.vars.get(key, "<undefined>")
        self.out.step("📖", f"GET {key} = {val}")
