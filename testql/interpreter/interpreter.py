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
from ._testtoon_parser import testtoon_to_iql
from ._api_runner import ApiRunnerMixin
from ._assertions import AssertionsMixin
from ._encoder import EncoderMixin
from ._flow import FlowMixin
from ._gui import GuiMixin
from ._dom_scan import DomScanMixin
from ._hardware import HardwareMixin
from ._shell import ShellMixin
from ._unit import UnitMixin
from ._websockets import WebSocketMixin
from .dispatcher import CommandDispatcher


class IqlInterpreter(ApiRunnerMixin, AssertionsMixin, EncoderMixin, FlowMixin, GuiMixin, DomScanMixin, HardwareMixin, ShellMixin, UnitMixin, WebSocketMixin, BaseInterpreter):
    """
    IQL interpreter — runs .testql.toon.yaml / .iql / .tql scripts.

    Supports both legacy IQL format and the new TestTOON tabular format.
    TestTOON files are automatically detected and expanded to IQL commands.

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
        # Handle bridge_url safely (BaseInterpreter in oqlos might not support it yet)
        try:
            super().__init__(variables=variables, quiet=quiet, bridge_url=bridge_url)
        except TypeError:
            super().__init__(variables=variables, quiet=quiet)
            self.bridge_url = bridge_url
        self.api_url = api_url
        self.dry_run = dry_run
        self.include_paths = include_paths or ["."]
        self.last_response: dict[str, Any] | None = None
        self.last_status: int = 0
        self.events: list[dict[str, Any]] = []
        self._included: set[str] = set()  # prevent circular includes
        self.dispatcher = CommandDispatcher(self)  # Central command dispatcher

    def parse(self, source: str, filename: str = "<string>") -> IqlScript:
        """Auto-detect format: TestTOON (.testql.toon.yaml) vs legacy IQL."""
        if self._is_testtoon(source, filename):
            return testtoon_to_iql(source, filename)
        return parse_iql(source, filename)

    @staticmethod
    def _is_testtoon(source: str, filename: str) -> bool:
        """Detect TestTOON format by extension or content."""
        if filename.endswith('.testql.yaml') or filename.endswith('.testql.toon.yaml') or filename.endswith('.testtoon'):
            return True
        # Content-based detection: look for TOON section headers
        import re
        return bool(re.search(r'^[A-Z_]+(?:\[\d+\])?\{[^}]+\}:', source, re.MULTILINE))

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
        """Dispatch command using central dispatcher with auto-discovery."""
        # Try dispatcher first (for registered _cmd_* handlers)
        if self.dispatcher.dispatch(cmd, args, line):
            return

        # Fallback to event emission for semantic commands
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
