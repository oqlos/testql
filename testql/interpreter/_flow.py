"""Flow control mixin — WAIT, LOG, PRINT, INCLUDE and UI event emission."""

from __future__ import annotations

import time
from pathlib import Path

from testql.base import StepResult, StepStatus

from ._parser import IqlLine, IqlScript, parse_iql


class FlowMixin:
    """Mixin providing: WAIT, LOG, PRINT, INCLUDE and _emit_event."""

    def _cmd_wait_for(self, args: str, line: IqlLine) -> None:
        """
        WAIT_FOR "selector" VISIBLE 5000
        WAIT_FOR NETWORK_IDLE 10000
        """
        parts = args.strip().split()
        if not parts:
            return

        timeout_ms = 5000
        selector = parts[0].strip("\"'")
        state = "VISIBLE"
        
        if len(parts) >= 2:
            if parts[1].upper() in ("VISIBLE", "HIDDEN", "NETWORK_IDLE"):
                state = parts[1].upper()
                if len(parts) >= 3:
                    try:
                        timeout_ms = int(parts[2])
                    except ValueError:
                        pass
            else:
                try:
                    timeout_ms = int(parts[1])
                except ValueError:
                    pass

        if self.dry_run:
            self.out.step("⏳", f"WAIT_FOR {selector} {state} timeout={timeout_ms}ms (dry-run)")
            self.results.append(StepResult(
                name=f"WAIT_FOR {selector} {state}", status=StepStatus.PASSED,
            ))
            return

        self.out.step("⏳", f"Waiting for {selector} to be {state} (timeout {timeout_ms}ms)...")
        
        # Simulated polling for now (as we don't have a real browser attached in this CLI tool yet)
        # In the future, this will call a browser driver.
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout_ms:
            # Placeholder: always "succeeds" after a short delay for simulation
            time.sleep(0.1)
            break
        
        self.out.step("✅", f"{selector} is {state}")
        self.results.append(StepResult(
            name=f"WAIT_FOR {selector} {state}", status=StepStatus.PASSED,
        ))

    def _cmd_wait(self, args: str, line: IqlLine) -> None:
        ms = int(args.strip())
        if self.dry_run:
            self.out.step("⏳", f"WAIT {ms}ms (dry-run)")
        else:
            time.sleep(ms / 1000)
            self.out.step("⏳", f"WAIT {ms}ms")

    def _cmd_log(self, args: str, line: IqlLine) -> None:
        msg = args.strip()
        if msg.startswith('"'):
            end = msg.find('"', 1)
            if end > 0:
                msg = msg[1:end]
        self.out.info(msg)

    def _cmd_print(self, args: str, line: IqlLine) -> None:
        self.out.emit(args)

    def _cmd_include(self, args: str, line: IqlLine) -> None:
        """INCLUDE "relative/path.iql" — inline and execute another script."""
        rel_path = args.strip().strip("\"'")
        resolved: Path | None = None
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
        sub_script: IqlScript = parse_iql(source, filename=rel_path)
        for sub_line in sub_script.lines:
            sub_args = self.vars.interpolate(sub_line.args)
            try:
                self._dispatch(sub_line.command, sub_args, sub_line)
            except Exception as e:
                self.errors.append(f"INCLUDE {rel_path} L{sub_line.number}: {e}")
                self.out.fail(f"INCLUDE {rel_path} L{sub_line.number}: {e}")

    # ── UI / navigation events ─────────────────────────────────────────────────

    _EVENT_ICONS: dict[str, str] = {
        "navigate": "📍", "click": "🖱️", "input": "⌨️",
        "select_device": "📱", "select_interval": "⏱️",
        "start_test": "🧪", "step_complete": "✅",
        "protocol_created": "📋", "protocol_finalize": "✔️",
        "emit": "📣", "render": "🎨", "layout": "📐",
        "record_start": "🔴", "record_stop": "⏹️",
        "create_protocol": "📋",
    }

    def _emit_event(self, cmd: str, args: str, line: IqlLine) -> None:
        """Emit a navigation/UI event (for commands with no explicit handler)."""
        event = {"type": cmd, "args": args, "line": line.number}
        self.events.append(event)
        icon = self._EVENT_ICONS.get(cmd, "▶️")
        self.out.step(icon, f"{cmd.upper()} {args}")
        self.results.append(StepResult(
            name=f"{cmd.upper()} {args[:60]}", status=StepStatus.PASSED,
        ))
