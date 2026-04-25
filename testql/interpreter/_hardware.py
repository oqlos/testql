"""Hardware commands mixin for IqlInterpreter — HARDWARE peripheral checks."""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import IqlLine


class HardwareMixin:
    """Mixin providing HARDWARE command support for peripheral checks."""

    def _hardware_url(self) -> str:
        return self.vars.get("hardware_url", "http://localhost:8202")

    def _hardware_do_http(
        self, method: str, url: str, body: dict | None, label: str
    ) -> tuple[int, dict]:
        """Execute hardware HTTP call and return (status, data)."""
        req_body = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(
            url, data=req_body, method=method,
            headers={"Content-Type": "application/json"} if req_body else {},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            text = resp.read().decode("utf-8")
            try:
                data = json.loads(text)
            except Exception:
                data = {"text": text[:200]}
            return status, data

    def _hardware_call(
        self, method: str, endpoint: str, body: dict | None, line: IqlLine, label: str
    ) -> None:
        url = f"{self._hardware_url()}{endpoint}"
        if self.dry_run:
            self.out.step("🔧", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return
        try:
            status, data = self._hardware_do_http(method, url, body, label)
            if status < 400:
                self.out.step("✅", f"{label} → {status}")
                self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=data))
            else:
                self.out.step("❌", f"{label} → {status}")
                self.results.append(StepResult(
                    name=label, status=StepStatus.FAILED, message=f"HTTP {status}", details=data
                ))
        except urllib.error.HTTPError as e:
            self.out.step("❌", f"{label} → {e.code}")
            self.results.append(StepResult(
                name=label, status=StepStatus.FAILED, message=f"HTTP {e.code}"
            ))
        except Exception as e:
            self.out.step("❌", f"{label} → {e}")
            self.results.append(StepResult(
                name=label, status=StepStatus.ERROR, message=str(e)
            ))

    def _cmd_hardware(self, args: str, line: IqlLine) -> None:
        """HARDWARE <command> <peripheral> — Execute hardware command.

        Examples:
            HARDWARE check piadc
            HARDWARE check motor-dri0050
            HARDWARE check modbus-io
            HARDWARE status piadc
            HARDWARE reset motor-dri0050
        """
        parts = args.strip().split()
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: HARDWARE requires <command> <peripheral>")
            return

        command = parts[0].lower()
        peripheral = parts[1]

        label = f"HARDWARE {command} {peripheral}"

        if command == "check":
            # Check if peripheral is available
            self._hardware_call("GET", f"/api/v1/hardware/{peripheral}", None, line, label)
        elif command == "status":
            # Get peripheral status
            self._hardware_call("GET", f"/api/v1/hardware/{peripheral}/status", None, line, label)
        elif command == "reset":
            # Reset peripheral
            self._hardware_call("POST", f"/api/v1/hardware/{peripheral}/reset", None, line, label)
        elif command == "configure":
            # Configure peripheral (requires JSON body)
            if len(parts) < 3:
                self.out.fail(f"L{line.number}: HARDWARE configure requires JSON body")
                return
            try:
                config = json.loads(" ".join(parts[2:]))
                self._hardware_call("POST", f"/api/v1/hardware/{peripheral}/configure", config, line, label)
            except json.JSONDecodeError:
                self.out.fail(f"L{line.number}: Invalid JSON for HARDWARE configure")
        else:
            self.out.warn(f"L{line.number}: Unknown HARDWARE command: {command}")
            self.results.append(StepResult(
                name=label, status=StepStatus.WARNING, message=f"Unknown command: {command}"
            ))
