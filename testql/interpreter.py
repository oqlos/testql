"""
testql/interpreter.py — TestQL (Interface Query Language) interpreter.

Executes .tql / .iql scripts with:
  - Variable interpolation (SET/GET, ${var})
  - Assertions (ASSERT_STATUS, ASSERT_CONTAINS, ASSERT_JSON)
  - INCLUDE for script composition
  - API calls with response capture
  - Browser navigation commands
  - Encoder control commands
  - Session recording/replay hooks
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import (
    BaseInterpreter,
    ScriptResult,
    StepResult,
    StepStatus,
)

# ═══════════════════════════════════════════════════════════════════════════════
# AST
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IqlLine:
    number: int
    command: str
    args: str
    raw: str

@dataclass
class IqlScript:
    filename: str = ""
    lines: list[IqlLine] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════════════════

def parse_iql(source: str, filename: str = "<string>") -> IqlScript:
    """Parse IQL source into command list."""
    script = IqlScript(filename=filename)
    for i, raw in enumerate(source.split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        script.lines.append(IqlLine(number=i, command=cmd, args=args, raw=line))
    return script

# ═══════════════════════════════════════════════════════════════════════════════
# Interpreter
# ═══════════════════════════════════════════════════════════════════════════════

class IqlInterpreter(BaseInterpreter):
    """
    IQL interpreter — runs .iql scripts.

    Features:
      - SET/GET variables with ${var} interpolation
      - API calls (GET/POST/PUT/DELETE) with response capture
      - ASSERT_STATUS, ASSERT_CONTAINS, ASSERT_JSON assertions
      - INCLUDE to compose scripts
      - NAVIGATE, CLICK, INPUT, SELECT_DEVICE, etc. (emit events)
      - WAIT, LOG, EMIT
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8101",
        variables: dict[str, Any] | None = None,
        quiet: bool = False,
        dry_run: bool = False,
        include_paths: list[str] | None = None,
    ):
        super().__init__(variables=variables, quiet=quiet)
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
            # Variable interpolation
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

    # ── Command dispatch ─────────────────────────────────────────────────

    def _dispatch(self, cmd: str, args: str, line: IqlLine) -> None:
        handler = getattr(self, f"_cmd_{cmd.lower()}", None)
        if handler:
            handler(args, line)
        else:
            # Treat as event emission (NAVIGATE, CLICK, etc.)
            self._emit_event(cmd.lower(), args, line)

    # ── Variables ────────────────────────────────────────────────────────

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

    # ── API calls ────────────────────────────────────────────────────────

    def _cmd_api(self, args: str, line: IqlLine) -> None:
        parts = args.strip().split(None, 2)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: API requires METHOD URL [body]")
            return

        method = parts[0].upper()
        url = parts[1].strip('"\'')
        body_str = parts[2] if len(parts) > 2 else ""

        # Resolve relative URLs
        if url.startswith("/"):
            url = f"{self.api_url}{url}"

        body_data = None
        if body_str:
            body_str = self.vars.interpolate(body_str)
            try:
                body_data = json.loads(body_str)
            except json.JSONDecodeError:
                body_data = {"raw": body_str}

        if self.dry_run:
            self.out.step("🌐", f"API {method} {url} (dry-run)")
            self.last_status = 200
            self.last_response = {"data": [], "_dry_run": True}
            self.results.append(StepResult(
                name=f"API {method} {url}", status=StepStatus.PASSED,
            ))
            return

        try:
            req_body = json.dumps(body_data).encode("utf-8") if body_data else None
            req = urllib.request.Request(
                url, data=req_body, method=method,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.last_status = resp.status
                text = resp.read().decode("utf-8")
                try:
                    self.last_response = json.loads(text)
                except Exception:
                    self.last_response = {"text": text[:500]}

            icon = "✅" if self.last_status < 400 else "❌"
            self.out.step(icon, f"API {method} {url} → {self.last_status}")

            # Store response data in variables
            self.vars.set("_status", self.last_status)
            self.vars.set("_response", self.last_response)
            if isinstance(self.last_response, dict):
                data = self.last_response.get("data")
                if isinstance(data, list):
                    self.vars.set("_count", len(data))

            self.results.append(StepResult(
                name=f"API {method} {url}", status=StepStatus.PASSED,
                details={"status": self.last_status},
            ))

        except urllib.error.HTTPError as e:
            self.last_status = e.code
            self.last_response = {}
            self.out.fail(f"API {method} {url} → {e.code}")
            self.results.append(StepResult(
                name=f"API {method} {url}", status=StepStatus.FAILED,
                message=f"HTTP {e.code}",
            ))
        except Exception as e:
            self.last_status = 0
            self.last_response = {}
            self.out.fail(f"API {method} {url} → {e}")
            self.results.append(StepResult(
                name=f"API {method} {url}", status=StepStatus.ERROR,
                message=str(e),
            ))

    # ── Assertions ───────────────────────────────────────────────────────

    def _cmd_assert_status(self, args: str, line: IqlLine) -> None:
        expected = int(args.strip())
        ok = self.last_status == expected
        if ok:
            self.out.step("  ✅", f"ASSERT_STATUS {expected}")
            self.results.append(StepResult(
                name=f"ASSERT_STATUS {expected}", status=StepStatus.PASSED,
            ))
        else:
            self.out.step("  ❌", f"ASSERT_STATUS {expected} (got {self.last_status})")
            self.errors.append(f"L{line.number}: expected status {expected}, got {self.last_status}")
            self.results.append(StepResult(
                name=f"ASSERT_STATUS {expected}", status=StepStatus.FAILED,
                message=f"expected {expected}, got {self.last_status}",
            ))

    def _cmd_assert_contains(self, args: str, line: IqlLine) -> None:
        needle = args.strip().strip('"\'')
        haystack = json.dumps(self.last_response or {})
        ok = needle in haystack
        if ok:
            self.out.step("  ✅", f"ASSERT_CONTAINS \"{needle}\"")
            self.results.append(StepResult(
                name=f"ASSERT_CONTAINS \"{needle}\"", status=StepStatus.PASSED,
            ))
        else:
            self.out.step("  ❌", f"ASSERT_CONTAINS \"{needle}\" — not found")
            self.errors.append(f"L{line.number}: \"{needle}\" not found in response")
            self.results.append(StepResult(
                name=f"ASSERT_CONTAINS \"{needle}\"", status=StepStatus.FAILED,
                message=f"\"{needle}\" not found",
            ))

    _COMPARE_OPS: dict[str, Any] = {
        "==": lambda a, b: a == b,
        "=":  lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">":  lambda a, b: (a or 0) > b,
        ">=": lambda a, b: (a or 0) >= b,
        "<":  lambda a, b: (a or 0) < b,
        "<=": lambda a, b: (a or 0) <= b,
    }

    @staticmethod
    def _navigate_json_path(root: Any, path: str) -> Any:
        """Navigate a dotted JSON path, with .length support for lists."""
        obj = root
        for key in path.split("."):
            if isinstance(obj, dict):
                obj = obj.get(key)
            elif isinstance(obj, list):
                try:
                    obj = obj[int(key)]
                except (ValueError, IndexError):
                    obj = None
            else:
                obj = None

        # Handle .length on lists
        if path.endswith(".length") and isinstance(root, dict):
            parent = root
            for key in path.rsplit(".", 1)[0].split("."):
                parent = parent.get(key) if isinstance(parent, dict) else None
            if isinstance(parent, list):
                obj = len(parent)
        return obj

    def _cmd_assert_json(self, args: str, line: IqlLine) -> None:
        """ASSERT_JSON path operator value — e.g. ASSERT_JSON data.length > 0"""
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.warn(f"L{line.number}: ASSERT_JSON requires <path> <op> <value>")
            return

        path, op, expected_str = parts[0], parts[1], parts[2]
        obj = self._navigate_json_path(self.last_response, path)

        try:
            expected = float(expected_str) if "." in expected_str else int(expected_str)
        except ValueError:
            expected = expected_str.strip('"\'')

        cmp_fn = self._COMPARE_OPS.get(op)
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

    def _cmd_assert_ok(self, args: str, line: IqlLine) -> None:
        """ASSERT_OK — checks last status was 2xx"""
        ok = 200 <= self.last_status < 300
        if ok:
            self.out.step("  ✅", f"ASSERT_OK (status {self.last_status})")
            self.results.append(StepResult(name="ASSERT_OK", status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"ASSERT_OK (status {self.last_status})")
            self.errors.append(f"L{line.number}: expected 2xx, got {self.last_status}")
            self.results.append(StepResult(
                name="ASSERT_OK", status=StepStatus.FAILED,
                message=f"status {self.last_status}",
            ))

    # ── INCLUDE ──────────────────────────────────────────────────────────

    def _cmd_include(self, args: str, line: IqlLine) -> None:
        rel_path = args.strip().strip('"\'')
        resolved = None
        for base in self.include_paths:
            candidate = Path(base) / rel_path
            if candidate.is_file():
                resolved = candidate
                break

        if not resolved:
            self.out.fail(f"L{line.number}: INCLUDE not found: {rel_path}")
            self.errors.append(f"INCLUDE not found: {rel_path}")
            return

        abs_path = str(resolved.resolve())
        if abs_path in self._included:
            self.out.warn(f"L{line.number}: circular INCLUDE skipped: {rel_path}")
            return

        self._included.add(abs_path)
        self.out.step("📎", f"INCLUDE {rel_path}")
        source = resolved.read_text(encoding="utf-8")
        sub_script = parse_iql(source, filename=rel_path)
        for sub_line in sub_script.lines:
            sub_args = self.vars.interpolate(sub_line.args)
            try:
                self._dispatch(sub_line.command, sub_args, sub_line)
            except Exception as e:
                self.errors.append(f"INCLUDE {rel_path} L{sub_line.number}: {e}")
                self.out.fail(f"INCLUDE {rel_path} L{sub_line.number}: {e}")

    # ── Flow control ─────────────────────────────────────────────────────

    def _cmd_wait(self, args: str, line: IqlLine) -> None:
        ms = int(args.strip())
        if self.dry_run:
            self.out.step("⏳", f"WAIT {ms}ms (dry-run)")
        else:
            time.sleep(ms / 1000)
            self.out.step("⏳", f"WAIT {ms}ms")

    def _cmd_log(self, args: str, line: IqlLine) -> None:
        # LOG "message" {"level": "info"}
        msg = args.strip()
        if msg.startswith('"'):
            end = msg.find('"', 1)
            if end > 0:
                msg = msg[1:end]
        self.out.info(msg)

    def _cmd_print(self, args: str, line: IqlLine) -> None:
        self.out.emit(args)

    # ── Encoder commands ──────────────────────────────────────────────────

    def _encoder_url(self) -> str:
        return self.vars.get("encoder_url", "http://localhost:8105")

    def _encoder_call(self, method: str, endpoint: str, body: dict | None, line: IqlLine, label: str) -> None:
        url = f"{self._encoder_url()}{endpoint}"
        if self.dry_run:
            self.out.step("🎛️", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return
        try:
            req_body = json.dumps(body).encode("utf-8") if body else None
            req = urllib.request.Request(
                url, data=req_body, method=method,
                headers={"Content-Type": "application/json"} if req_body else {},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("utf-8")
                try:
                    data = json.loads(text)
                except Exception:
                    data = {"text": text[:200]}
                self.vars.set("_encoder_status", data)
                self.out.step("🎛️", f"{label} => {json.dumps(data)[:120]}")
                self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=data))
        except Exception as e:
            self.out.fail(f"{label} => {e}")
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(e)))

    def _cmd_encoder_on(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/activate", None, line, "ENCODER_ON")

    def _cmd_encoder_off(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/deactivate", None, line, "ENCODER_OFF")

    def _cmd_encoder_scroll(self, args: str, line: IqlLine) -> None:
        delta = int(args.strip()) if args.strip() else 1
        self._encoder_call("POST", "/encoder/scroll", {"delta": delta}, line, f"ENCODER_SCROLL {delta}")

    def _cmd_encoder_click(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/click", None, line, "ENCODER_CLICK")

    def _cmd_encoder_dblclick(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/cancel", None, line, "ENCODER_DBLCLICK")

    def _cmd_encoder_focus(self, args: str, line: IqlLine) -> None:
        zone = args.strip().strip('"\'') or "col3"
        self._encoder_call("POST", "/encoder/focus", {"zone": zone}, line, f"ENCODER_FOCUS {zone}")

    def _cmd_encoder_status(self, args: str, line: IqlLine) -> None:
        self._encoder_call("GET", "/encoder/status", None, line, "ENCODER_STATUS")

    def _cmd_encoder_page_next(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/page-next", None, line, "ENCODER_PAGE_NEXT")

    def _cmd_encoder_page_prev(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/page-prev", None, line, "ENCODER_PAGE_PREV")

    # ── Navigation / UI events ───────────────────────────────────────────

    def _emit_event(self, cmd: str, args: str, line: IqlLine) -> None:
        """Emit a navigation/UI event."""
        event = {"type": cmd, "args": args, "line": line.number}
        self.events.append(event)

        icons = {
            "navigate": "📍", "click": "🖱️", "input": "⌨️",
            "select_device": "📱", "select_interval": "⏱️",
            "start_test": "🧪", "step_complete": "✅",
            "protocol_created": "📋", "protocol_finalize": "✔️",
            "emit": "📣", "render": "🎨", "layout": "📐",
            "record_start": "🔴", "record_stop": "⏹️",
            "create_protocol": "📋",
        }
        icon = icons.get(cmd, "▶️")
        self.out.step(icon, f"{cmd.upper()} {args}")
        self.results.append(StepResult(
            name=f"{cmd.upper()} {args[:60]}", status=StepStatus.PASSED,
        ))

# ═══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="IQL Interpreter — Interface Query Language")
    parser.add_argument("file", nargs="?", help="IQL file to execute")
    parser.add_argument("-u", "--url", default="http://localhost:8101",
                        help="Backend API URL (default: http://localhost:8101)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Dry-run mode (no API calls)")
    parser.add_argument("-v", "--var", action="append", default=[],
                        help="Set variable: name=value")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    parser.add_argument("-c", "--command", help="Execute single command")

    args = parser.parse_args()

    # Parse variable overrides
    variables: dict[str, Any] = {}
    for v in args.var:
        if "=" in v:
            k, val = v.split("=", 1)
            variables[k.strip()] = val.strip()

    interp = IqlInterpreter(
        api_url=args.url, variables=variables,
        quiet=args.quiet, dry_run=args.dry_run,
    )

    if args.command:
        result = interp.run(args.command, filename="<command>")
    elif args.file:
        # Set include paths to file's directory + cwd
        file_dir = str(Path(args.file).parent.resolve())
        interp.include_paths = [file_dir, "."]
        result = interp.run_file(args.file)
    else:
        parser.print_help()
        return

    if args.json:
        print(json.dumps({
            "source": result.source,
            "ok": result.ok,
            "passed": result.passed,
            "failed": result.failed,
            "total": len(result.steps),
            "duration_ms": round(result.duration_ms, 1),
            "errors": result.errors,
            "warnings": result.warnings,
            "variables": {k: str(v) for k, v in result.variables.items()},
        }, indent=2, ensure_ascii=False))

    exit(0 if result.ok else 1)

if __name__ == "__main__":
    main()
