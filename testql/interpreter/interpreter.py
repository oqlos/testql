"""
testql.interpreter.interpreter
— OQL / TestQL interpreter (refactored into subpackage).

Import path unchanged: `from testql.interpreter import OqlInterpreter`
"""

from __future__ import annotations

import os
import shlex
import time
from typing import Any

from testql.base import BaseInterpreter, ScriptResult, StepResult, StepStatus

from ._parser import OqlLine, OqlScript, parse_oql
from ._testtoon_parser import testtoon_to_oql
from ._api_runner import ApiRunnerMixin
from ._assertions import AssertionsMixin
from ._context import ContextMixin
from ._encoder import EncoderMixin
from ._flow import FlowMixin
from ._gui import GuiMixin
from ._desktop import DesktopMixin
from ._dom_scan import DomScanMixin
from ._hardware import HardwareMixin
from ._modbus import ModbusMixin
from ._shell import ShellMixin
from ._unit import UnitMixin
from ._validation import ValidationMixin
from ._websockets import WebSocketMixin
from .dispatcher import CommandDispatcher


class OqlInterpreter(ApiRunnerMixin, AssertionsMixin, ContextMixin, EncoderMixin, FlowMixin, GuiMixin, DesktopMixin, DomScanMixin, HardwareMixin, ModbusMixin, ShellMixin, UnitMixin, ValidationMixin, WebSocketMixin, BaseInterpreter):
    """
    OQL interpreter — runs .testql.toon.yaml / .oql / .tql scripts.

    Supports both legacy OQL format and the new TestTOON tabular format.
    TestTOON files are automatically detected and expanded to OQL commands.

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
        timeout_ms: int | None = None,
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
        self.timeout_ms = timeout_ms
        self.last_response: dict[str, Any] | None = None
        self.last_status: int = 0
        self.events: list[dict[str, Any]] = []
        self._included: set[str] = set()  # prevent circular includes
        self._secret_variable_names: set[str] = set()
        self._secret_values: set[str] = set()
        self.dispatcher = CommandDispatcher(self)  # Central command dispatcher

    def parse(self, source: str, filename: str = "<string>") -> OqlScript:
        """Auto-detect format: TestTOON (.testql.toon.yaml) vs legacy OQL."""
        if self._is_testtoon(source, filename):
            return testtoon_to_oql(source, filename)
        return parse_oql(source, filename)

    @staticmethod
    def _is_testtoon(source: str, filename: str) -> bool:
        """Detect TestTOON format by extension or content."""
        if filename.endswith('.testql.yaml') or filename.endswith('.testql.toon.yaml') or filename.endswith('.testtoon'):
            return True
        # Content-based detection: look for TOON section headers
        import re
        return bool(re.search(r'^[A-Z_]+(?:\[\d+\])?\{[^}]+\}:', source, re.MULTILINE))

    def execute(self, parsed: OqlScript) -> ScriptResult:
        t0 = time.monotonic()
        self.out.step("📜", f"OQL: {parsed.filename}")

        try:
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
        finally:
            # A failed assertion can prevent GUI_STOP from being reached. Never
            # leave Chromium/WebDriver processes behind after a scenario.
            close_gui = getattr(self, "_close_gui_session", None)
            if callable(close_gui) and self._gui_app:
                try:
                    close_gui()
                except Exception as e:
                    self.warnings.append(f"GUI cleanup failed: {e}")

        elapsed = (time.monotonic() - t0) * 1000
        ok = all(r.status in (StepStatus.PASSED, StepStatus.SKIPPED) for r in self.results)
        reported_variables = self.vars.all()
        for name in self._secret_variable_names:
            if name in reported_variables:
                reported_variables[name] = "***REDACTED***"
        sr = ScriptResult(
            source=parsed.filename, ok=ok, steps=self.results,
            variables=reported_variables, errors=self.errors,
            warnings=self.warnings, duration_ms=elapsed,
        )
        self.out.emit("")
        self.out.emit(sr.summary())
        return sr

    # ── Command dispatch ──────────────────────────────────────────────────────

    def _dispatch(self, cmd: str, args: str, line: OqlLine) -> None:
        """Dispatch command using central dispatcher with auto-discovery."""
        # Try dispatcher first (for registered _cmd_* handlers)
        if self.dispatcher.dispatch(cmd, args, line):
            return

        # Fallback to event emission for semantic commands
        self._emit_event(cmd.lower(), args, line)

    # ── Variables ─────────────────────────────────────────────────────────────

    def _cmd_set(self, args: str, line: OqlLine) -> None:
        # Handle quoted keys with spaces: SET "key with spaces" "value"
        import shlex
        try:
            parts = shlex.split(args)
            if len(parts) < 2:
                self.out.warn(f"L{line.number}: SET requires <name> <value>")
                return
            key, val = parts[0], parts[1]
            # Strip quotes from value if present
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            self.vars.set(key, val)
            self.out.step("📝", f'SET "{key}" = "{val}"')
        except ValueError:
            # Fallback to simple split if shlex fails
            parts = args.split(None, 1)
            if len(parts) < 2:
                self.out.warn(f"L{line.number}: SET requires <name> <value>")
                return
            key, val = parts[0], parts[1].strip().strip('"\'')
            self.vars.set(key, val)
            self.out.step("📝", f"SET {key} = {val}")

    def _cmd_get(self, args: str, line: OqlLine) -> None:
        key = args.strip()
        val = self.vars.get(key, "<undefined>")
        self.out.step("📖", f"GET {key} = {val}")

    def _cmd_getenv_secret(self, args: str, line: OqlLine) -> None:
        """GETENV_SECRET ENV_NAME [variable] — import an environment secret without logging it."""
        parts = shlex.split(args)
        if not parts or len(parts) > 2:
            raise ValueError("GETENV_SECRET requires ENV_NAME and optional variable name")
        env_name = parts[0]
        variable_name = parts[1] if len(parts) == 2 else env_name.lower()
        value = os.environ.get(env_name, "")
        if not value:
            raise ValueError(f"required secret environment variable is missing: {env_name}")
        self.vars.set(variable_name, value)
        self._secret_variable_names.add(variable_name)
        self._secret_values.add(value)
        self.out.step("🔐", f'GETENV_SECRET "{env_name}" → "{variable_name}" (configured, redacted)')
        self.results.append(StepResult(
            name=f'GETENV_SECRET "{env_name}"', status=StepStatus.PASSED
        ))

    def is_secret_value(self, value: str) -> bool:
        return any(secret and secret in value for secret in self._secret_values)
