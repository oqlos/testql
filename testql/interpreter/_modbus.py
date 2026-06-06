"""Modbus RTU probe mixin — direct bus scan via external probe script or HTTP wizard API."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class ModbusMixin:
    """MODBUS probe / API wizard helpers for TestQL automation."""

    def _modbus_probe_script(self) -> Path:
        raw = self.vars.get(
            "modbus_probe_script",
            os.environ.get(
                "TESTQL_MODBUS_PROBE_SCRIPT",
                "/home/tom/github/maskservice/c2004/testql-testing/scripts/testql-modbus-probe.py",
            ),
        )
        return Path(str(raw)).expanduser()

    def _modbus_store_response(self, data: dict[str, Any], label: str) -> None:
        self.last_response = data
        self.vars.set("_modbus_probe", data)
        self.vars.set("_modbus_last", data)

    def _modbus_skip_enabled(self) -> bool:
        flag = str(
            self.vars.get("modbus_skip_if_unavailable", os.environ.get("TESTQL_MODBUS_SKIP", ""))
        ).lower()
        return flag in {"1", "true", "yes", "on"}

    def _modbus_serial_exists(self, serial: str) -> bool:
        if not serial or serial == "-":
            serial = os.environ.get("MODBUS_SERIAL", "")
        if not serial:
            return False
        return Path(serial).exists()

    @staticmethod
    def _modbus_parse_kv_args(parts: list[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        for item in parts:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            out[key.strip().lower()] = value.strip()
        return out

    def _execute_probe_script(
        self, script: Path, env: dict[str, str], timeout_s: float, label: str
    ) -> subprocess.CompletedProcess | None:
        """Execute probe script subprocess; return None on failure."""
        try:
            return subprocess.run(
                [os.environ.get("TESTQL_PYTHON", "python3"), str(script), "--emit-json"],
                capture_output=True,
                text=True,
                timeout=max(5.0, timeout_s),
                env=env,
                cwd=str(script.parent),
            )
        except subprocess.TimeoutExpired:
            self.out.fail(f"{label} timeout after {timeout_s}s")
            self.results.append(
                StepResult(name=label, status=StepStatus.FAILED, message="probe timeout")
            )
        except Exception as exc:
            self.out.fail(f"{label}: {exc}")
            self.results.append(StepResult(name=label, status=StepStatus.ERROR, message=str(exc)))
        return None

    def _parse_probe_response(
        self, proc: subprocess.CompletedProcess
    ) -> dict[str, Any]:
        """Parse probe script output into structured data dict."""
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if not stdout:
            return {"ok": False, "error": "empty stdout", "stderr": stderr, "exit_code": proc.returncode}
        try:
            data = json.loads(stdout)
            data["exit_code"] = proc.returncode
            return data
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error": "invalid JSON from probe",
                "stdout": stdout[:500],
                "stderr": stderr[:500],
                "exit_code": proc.returncode,
            }

    def _emit_probe_result(self, data: dict[str, Any], label: str) -> bool:
        """Emit probe result and append to results; return True on success."""
        proc_ok = data.get("exit_code") == 0 and data.get("ok")
        if proc_ok:
            hits = sum(1 for row in data.get("results", []) if row.get("ok"))
            self.out.step("✅", f"{label} → ok ({hits} hit(s))")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=data))
            return True

        if self._modbus_skip_enabled():
            self.out.warn(f"{label} failed — skipped (TESTQL_MODBUS_SKIP)")
            self.results.append(
                StepResult(name=label, status=StepStatus.SKIPPED, message=data.get("error", "probe failed"))
            )
            return False

        self.out.step("❌", f"{label} → exit {data.get('exit_code')}")
        self.results.append(
            StepResult(name=label, status=StepStatus.FAILED, message=data.get("error", "probe failed"), details=data)
        )
        return False

    def _modbus_run_probe_script(
        self, line: OqlLine, label: str, extra_env: dict[str, str] | None = None
    ) -> bool:
        script = self._modbus_probe_script()
        if self.dry_run:
            self.out.step("🔌", f"{label} (dry-run)")
            self._modbus_store_response(
                {"ok": True, "dry_run": True, "results": [{"ok": True, "dry_run": True}]},
                label,
            )
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return True

        if not script.is_file():
            msg = f"Modbus probe script not found: {script}"
            if self._modbus_skip_enabled():
                self.out.warn(msg)
                self.results.append(StepResult(name=label, status=StepStatus.SKIPPED, message=msg))
                return False
            self.out.fail(msg)
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=msg))
            return False

        env = {**os.environ, **(extra_env or {})}
        timeout_s = float(self.vars.get("modbus_probe_timeout_s", env.get("MODBUS_PROBE_TIMEOUT", "45")))
        proc = self._execute_probe_script(script, env, timeout_s, label)
        if proc is None:
            return False

        data = self._parse_probe_response(proc)
        self._modbus_store_response(data, label)
        return self._emit_probe_result(data, label)

    def _cmd_modbus(self, args: str, line: OqlLine) -> None:
        """MODBUS <action> [key=value ...] — RTU probe or HTTP wizard helpers.

        Examples:
            MODBUS probe
            MODBUS probe serial=/dev/ttyACM1 baud=9600 device_ids=1,2
            MODBUS skip_if_no_port serial=/dev/ttyACM1
            MODBUS api plan
            MODBUS api runtime-status
        """
        parts = shlex.split(args) if args.strip() else []
        if not parts:
            self.out.fail(f"L{line.number}: MODBUS requires action")
            return

        action = parts[0].lower()
        kv = self._modbus_parse_kv_args(parts[1:])
        label = f"MODBUS {action}"

        if action == "skip_if_no_port":
            serial = kv.get("serial", os.environ.get("MODBUS_SERIAL", "-"))
            if not self._modbus_serial_exists(serial):
                self.out.warn(f"{label}: port missing ({serial})")
                self.vars.set("modbus_skip_probe", "1")
                self.results.append(
                    StepResult(name=label, status=StepStatus.SKIPPED, message=f"no port {serial}")
                )
                return
            self.vars.set("modbus_skip_probe", "0")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return

        if action == "probe":
            if str(self.vars.get("modbus_skip_probe", "0")) == "1":
                self._modbus_store_response({"ok": True, "skipped": True, "results": []}, label)
                self.out.warn(f"{label}: skipped (port unavailable)")
                self.results.append(StepResult(name=label, status=StepStatus.SKIPPED, message="prior skip"))
                return
            env: dict[str, str] = {}
            for key, env_name in (
                ("serial", "MODBUS_SERIAL"),
                ("baud", "MODBUS_BAUD"),
                ("parity", "MODBUS_PARITY"),
                ("device_ids", "MODBUS_DEVICE_IDS"),
                ("function", "MODBUS_FUNCTIONS"),
            ):
                if key in kv and kv[key] not in {"", "-"}:
                    env[env_name] = kv[key]
            self._modbus_run_probe_script(line, label, env)
            return

        if action == "api":
            sub = kv.get("endpoint", "").lower()
            if not sub and len(parts) > 1:
                sub = parts[1].lower()
            base = str(self.vars.get("modbus_api_url", os.environ.get("TESTQL_MODBUS_API_URL", "http://localhost:8096")))
            endpoints = {
                "plan": ("GET", "/api/v3/hardware/modbus/wizard/plan"),
                "runtime-status": ("GET", "/api/v3/hardware/runtime/status"),
                "runtime_status": ("GET", "/api/v3/hardware/runtime/status"),
                "status": ("GET", "/api/v3/hardware/runtime/status"),
            }
            spec = endpoints.get(sub.replace("_", "-"))
            if not spec:
                self.out.fail(f"L{line.number}: unknown MODBUS api target '{sub}'")
                return
            method, path = spec
            prev_url = self.api_url
            self.api_url = base.rstrip("/")
            try:
                self._cmd_api(f"{method} {path}", line)
            finally:
                self.api_url = prev_url
            return

        self.out.fail(f"L{line.number}: unknown MODBUS action '{action}'")
