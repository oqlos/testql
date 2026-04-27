"""Unit test execution mixin for OqlInterpreter — pytest integration."""

from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class UnitMixin:
    """Mixin providing unit test execution: UNIT_PYTEST, UNIT_IMPORT, UNIT_ASSERT."""

    _last_unit_result: dict[str, Any] | None = None

    def _parse_pytest_args(self, args: str) -> tuple[str, str, int]:
        """Parse UNIT_PYTEST arguments into (test_path, extra_args, timeout_ms)."""
        parts = args.strip().split(None, 1)
        if not parts:
            return "", "", 60000

        test_path = parts[0].strip('"\'')
        extra_args = parts[1] if len(parts) > 1 else ""
        timeout_ms = 60000

        # Extract timeout if specified
        if extra_args and extra_args.split()[-1].isdigit():
            parts_extra = extra_args.rsplit(None, 1)
            if parts_extra[-1].isdigit():
                timeout_ms = int(parts_extra[-1])
                extra_args = parts_extra[0]

        return test_path, extra_args, timeout_ms

    def _extract_pytest_summary(self, stdout: str) -> dict[str, str]:
        """Extract summary line from pytest stdout."""
        for line in stdout.split('\n'):
            if "passed" in line and "failed" in line:
                return {"summary": line}
        return {}

    def _run_pytest_subprocess(self, test_path: str, extra_args: str, timeout_ms: int) -> subprocess.CompletedProcess:
        """Execute pytest subprocess and return result."""
        cmd = [sys.executable, "-m", "pytest", test_path]
        if extra_args:
            cmd.extend(extra_args.split())

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000,
            cwd=str(Path.cwd()),
        )

    def _handle_pytest_dry_run(self, test_path: str, timeout_ms: int) -> None:
        """Handle UNIT_PYTEST in dry-run mode."""
        self.out.step("🧪", f'UNIT_PYTEST "{test_path[:50]}" [{timeout_ms}ms] (dry-run)')
        self._last_unit_result = {
            "path": test_path,
            "exit_code": 0,
            "passed": 1,
            "failed": 0,
            "dry_run": True,
        }
        self.results.append(StepResult(
            name=f'UNIT_PYTEST "{test_path[:40]}"', status=StepStatus.PASSED
        ))

    def _handle_pytest_success(self, test_path: str, result: subprocess.CompletedProcess) -> None:
        """Handle successful pytest execution."""
        passed = result.returncode == 0
        summary = self._extract_pytest_summary(result.stdout)

        self._last_unit_result = {
            "path": test_path,
            "exit_code": result.returncode,
            "passed": passed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "summary": summary,
        }

        icon = "✅" if passed else "❌"
        status = StepStatus.PASSED if passed else StepStatus.FAILED

        self.out.step(icon, f'UNIT_PYTEST "{test_path[:50]}" → exit {result.returncode}')
        self.results.append(StepResult(
            name=f'UNIT_PYTEST "{test_path[:40]}"',
            status=status,
            details={"exit_code": result.returncode, "summary": summary},
        ))

    def _handle_pytest_error(self, test_path: str, error: Exception, timeout_ms: int | None = None) -> None:
        """Handle pytest execution errors."""
        if isinstance(error, subprocess.TimeoutExpired):
            message = f"Timeout after {timeout_ms}ms" if timeout_ms else "Timeout"
        else:
            message = str(error)

        self.out.fail(f"UNIT_PYTEST error: {message}")
        self.results.append(StepResult(
            name=f'UNIT_PYTEST "{test_path[:40]}"',
            status=StepStatus.ERROR,
            message=message,
        ))

    def _cmd_unit_pytest(self, args: str, line: OqlLine) -> None:
        """UNIT_PYTEST "path/to/test.py" [timeout_ms] — Run pytest on specific file.

        Examples:
            UNIT_PYTEST "tests/test_main.py"
            UNIT_PYTEST "tests/" 30000
            UNIT_PYTEST "tests/test_api.py -v"
        """
        test_path, extra_args, timeout_ms = self._parse_pytest_args(args)
        if not test_path:
            self.out.fail(f"L{line.number}: UNIT_PYTEST requires path argument")
            return

        if self.dry_run:
            self._handle_pytest_dry_run(test_path, timeout_ms)
            return

        try:
            result = self._run_pytest_subprocess(test_path, extra_args, timeout_ms)
            self._handle_pytest_success(test_path, result)
        except Exception as e:
            self._handle_pytest_error(test_path, e, timeout_ms)

    def _cmd_unit_pytest_discover(self, args: str, line: OqlLine) -> None:
        """UNIT_PYTEST_DISCOVER "tests/" [timeout_ms] — Discover and run all tests.

        Examples:
            UNIT_PYTEST_DISCOVER "tests/"
            UNIT_PYTEST_DISCOVER "tests/" 120000
        """
        parts = args.strip().split(None, 1)
        if not parts:
            self.out.fail(f"L{line.number}: UNIT_PYTEST_DISCOVER requires path argument")
            return

        test_dir = parts[0].strip('"\'')
        timeout_ms = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 120000

        if self.dry_run:
            self.out.step("🧪", f'UNIT_PYTEST_DISCOVER "{test_dir[:50]}" (dry-run)')
            self.results.append(StepResult(
                name=f'UNIT_PYTEST_DISCOVER "{test_dir[:40]}"', status=StepStatus.PASSED
            ))
            return

        # Reuse UNIT_PYTEST with directory
        self._cmd_unit_pytest(f'"{test_dir}" {timeout_ms}', line)

    def _cmd_unit_import(self, args: str, line: OqlLine) -> None:
        """UNIT_IMPORT "module" — Verify module can be imported.

        Examples:
            UNIT_IMPORT "testql"
            UNIT_IMPORT "numpy"
        """
        module_name = args.strip().strip('"\'')
        if not module_name:
            self.out.fail(f"L{line.number}: UNIT_IMPORT requires module name")
            return

        if self.dry_run:
            self.out.step("📦", f'UNIT_IMPORT "{module_name}" (dry-run)')
            self.results.append(StepResult(
                name=f'UNIT_IMPORT "{module_name}"', status=StepStatus.PASSED
            ))
            return

        try:
            __import__(module_name)
            self.out.step("✅", f'UNIT_IMPORT "{module_name}"')
            self.results.append(StepResult(
                name=f'UNIT_IMPORT "{module_name}"', status=StepStatus.PASSED
            ))
        except ImportError as e:
            self.out.fail(f'UNIT_IMPORT "{module_name}" failed: {e}')
            self.results.append(StepResult(
                name=f'UNIT_IMPORT "{module_name}"',
                status=StepStatus.FAILED,
                message=str(e),
            ))
        except Exception as e:
            self.out.fail(f'UNIT_IMPORT "{module_name}" error: {e}')
            self.results.append(StepResult(
                name=f'UNIT_IMPORT "{module_name}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_unit_assert(self, args: str, line: OqlLine) -> None:
        """UNIT_ASSERT "module.function" "args_json" "expected" — Assert function returns expected value.

        Examples:
            UNIT_ASSERT "math.sqrt" "[4]" "2.0"
            UNIT_ASSERT "len" "[[1,2,3]]" "3"
        """
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.fail(f"L{line.number}: UNIT_ASSERT requires module.function, args, expected")
            return

        func_path = parts[0].strip('"\'')
        args_json = parts[1].strip('"\'')
        expected_str = parts[2].strip('"\'')

        if self.dry_run:
            self.out.step("🧪", f'UNIT_ASSERT "{func_path[:40]}" (dry-run)')
            self.results.append(StepResult(
                name=f'UNIT_ASSERT "{func_path[:30]}"', status=StepStatus.PASSED
            ))
            return

        try:
            # Parse module and function name
            if "." in func_path:
                module_name, func_name = func_path.rsplit(".", 1)
                module = __import__(module_name)
                for attr in module_name.split(".")[1:]:
                    module = getattr(module, attr)
                func = getattr(module, func_name)
            else:
                func = __import__("builtins").__dict__[func_path]

            # Parse args
            import json
            args_list = json.loads(args_json) if args_json else []

            # Call function
            result = func(*args_list)

            # Compare with expected
            import json as _json
            try:
                expected = json.loads(expected_str)
            except json.JSONDecodeError:
                expected = expected_str

            passed = result == expected

            icon = "✅" if passed else "❌"
            status = StepStatus.PASSED if passed else StepStatus.FAILED

            self.out.step(icon, f'UNIT_ASSERT "{func_path[:30]}" → {result} (expected {expected})')
            self.results.append(StepResult(
                name=f'UNIT_ASSERT "{func_path[:30]}"',
                status=status,
                details={"actual": result, "expected": expected},
            ))

        except Exception as e:
            self.out.fail(f'UNIT_ASSERT "{func_path}" error: {e}')
            self.results.append(StepResult(
                name=f'UNIT_ASSERT "{func_path[:30]}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))
