"""Shell execution mixin for OqlInterpreter — CLI/Shell test commands."""

from __future__ import annotations

import subprocess
import shlex
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class ShellMixin:
    """Mixin providing shell command execution: SHELL, EXEC, RUN, ASSERT_EXIT_CODE, etc."""

    # Store last shell execution result
    _last_shell_result: dict[str, Any] | None = None

    def _cmd_shell(self, args: str, line: OqlLine) -> None:
        """SHELL "command" [timeout_ms] — Execute arbitrary shell command.

        Examples:
            SHELL "ls -la"
            SHELL "python --version" 5000
            SHELL "cat file.txt | grep pattern" 10000
        """
        args_clean = args.strip()
        if not args_clean:
            self.out.fail(f"L{line.number}: SHELL requires command argument")
            return

        # Parse: "command with spaces" [timeout] or command [timeout]
        if args_clean.startswith('"') or args_clean.startswith("'"):
            # Quoted command - find closing quote
            quote = args_clean[0]
            close_idx = args_clean.find(quote, 1)
            if close_idx == -1:
                self.out.fail(f"L{line.number}: SHELL unclosed quote in command")
                return
            command = args_clean[1:close_idx]
            rest = args_clean[close_idx + 1:].strip()
            timeout_ms = 30000
            if rest:
                try:
                    timeout_ms = int(rest.split()[0])
                except (ValueError, IndexError):
                    pass
        else:
            # Unquoted - split by whitespace
            parts = args_clean.split(None, 1)
            command = parts[0]
            timeout_ms = 30000
            if len(parts) > 1:
                try:
                    timeout_ms = int(parts[1].split()[0])
                except (ValueError, IndexError):
                    pass

        timeout_sec = timeout_ms / 1000

        if self.dry_run:
            self.out.step("💻", f'SHELL "{command[:60]}" [{timeout_ms}ms] (dry-run)')
            self._last_shell_result = {
                "command": command,
                "returncode": 0,
                "stdout": "",
                "stderr": "",
                "dry_run": True,
            }
            self.results.append(StepResult(
                name=f'SHELL "{command[:40]}"', status=StepStatus.PASSED
            ))
            return

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            self._last_shell_result = {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            icon = "✅" if result.returncode == 0 else "⚠️"
            status = StepStatus.PASSED if result.returncode == 0 else StepStatus.WARNING

            self.out.step(icon, f'SHELL "{command[:50]}" → exit {result.returncode}')
            self.results.append(StepResult(
                name=f'SHELL "{command[:40]}"',
                status=status,
                details={"returncode": result.returncode, "stdout_len": len(result.stdout)},
            ))

        except subprocess.TimeoutExpired:
            self._last_shell_result = {"command": command, "returncode": -1, "timeout": True}
            self.out.fail(f"SHELL timeout after {timeout_ms}ms")
            self.results.append(StepResult(
                name=f'SHELL "{command[:40]}"',
                status=StepStatus.ERROR,
                message=f"Timeout after {timeout_ms}ms",
            ))
        except Exception as e:
            self._last_shell_result = {"command": command, "returncode": -1, "error": str(e)}
            self.out.fail(f"SHELL error: {e}")
            self.results.append(StepResult(
                name=f'SHELL "{command[:40]}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_exec(self, args: str, line: OqlLine) -> None:
        """EXEC "path/to/script" [args] [timeout_ms] — Execute script file.

        Examples:
            EXEC "./deploy.sh"
            EXEC "scripts/setup.py" "--force" 10000
        """
        parts = shlex.split(args.strip())
        if not parts:
            self.out.fail(f"L{line.number}: EXEC requires script path")
            return

        script_path = Path(parts[0].strip('"\''))
        script_args = parts[1:-1] if len(parts) > 2 and parts[-1].isdigit() else parts[1:]
        timeout_ms = int(parts[-1]) if parts and parts[-1].isdigit() else 30000

        if not script_path.exists():
            self.out.fail(f"EXEC: Script not found: {script_path}")
            self.results.append(StepResult(
                name=f'EXEC "{script_path}"', status=StepStatus.FAILED, message="Script not found"
            ))
            return

        command = str(script_path) + (" " + " ".join(script_args) if script_args else "")
        # Reuse SHELL logic
        self._cmd_shell(f'"{command}" {timeout_ms}', line)

    def _cmd_run(self, args: str, line: OqlLine) -> None:
        """RUN "python -m module" [args] [timeout_ms] — Run Python module.

        Examples:
            RUN "python -m pytest" "tests/" 60000
            RUN "python -m myapp" "--version"
        """
        parts = shlex.split(args.strip())
        if not parts:
            self.out.fail(f"L{line.number}: RUN requires command")
            return

        command = parts[0]
        extra_args = parts[1:-1] if len(parts) > 2 and parts[-1].isdigit() else parts[1:]
        timeout_ms = int(parts[-1]) if parts and parts[-1].isdigit() else 30000

        full_command = command + (" " + " ".join(extra_args) if extra_args else "")
        # Reuse SHELL logic
        self._cmd_shell(f'"{full_command}" {timeout_ms}', line)

    def _cmd_assert_exit_code(self, args: str, line: OqlLine) -> None:
        """ASSERT_EXIT_CODE <code> — Assert last shell command exit code.

        Examples:
            SHELL "myapp --version"
            ASSERT_EXIT_CODE 0
        """
        if self._last_shell_result is None:
            self.out.warn(f"L{line.number}: ASSERT_EXIT_CODE: No previous SHELL/EXEC/RUN command")
            return

        expected = int(args.strip())
        actual = self._last_shell_result.get("returncode", -999)

        if actual == expected:
            self.out.step("  ✅", f"ASSERT_EXIT_CODE {expected}")
            self.results.append(StepResult(
                name=f"ASSERT_EXIT_CODE {expected}", status=StepStatus.PASSED
            ))
        else:
            self.out.step("  ❌", f"ASSERT_EXIT_CODE {expected} (got {actual})")
            self.errors.append(f"L{line.number}: Expected exit code {expected}, got {actual}")
            self.results.append(StepResult(
                name=f"ASSERT_EXIT_CODE {expected}",
                status=StepStatus.FAILED,
                message=f"Expected {expected}, got {actual}",
            ))

    def _cmd_assert_stdout_contains(self, args: str, line: OqlLine) -> None:
        """ASSERT_STDOUT_CONTAINS "pattern" — Assert stdout contains pattern.

        Examples:
            SHELL "myapp --help"
            ASSERT_STDOUT_CONTAINS "--version"
        """
        if self._last_shell_result is None:
            self.out.warn(f"L{line.number}: ASSERT_STDOUT_CONTAINS: No previous SHELL command")
            return

        pattern = args.strip().strip('"\'')
        stdout = self._last_shell_result.get("stdout", "")

        if pattern in stdout:
            self.out.step("  ✅", f'ASSERT_STDOUT_CONTAINS "{pattern}"')
            self.results.append(StepResult(
                name=f'ASSERT_STDOUT "{pattern}"', status=StepStatus.PASSED
            ))
        else:
            self.out.step("  ❌", f'ASSERT_STDOUT_CONTAINS "{pattern}"')
            self.errors.append(f'L{line.number}: Pattern "{pattern}" not found in stdout')
            self.results.append(StepResult(
                name=f'ASSERT_STDOUT "{pattern}"',
                status=StepStatus.FAILED,
                message=f'Pattern "{pattern}" not found',
            ))

    def _cmd_assert_stderr_contains(self, args: str, line: OqlLine) -> None:
        """ASSERT_STDERR_CONTAINS "pattern" — Assert stderr contains pattern."""
        if self._last_shell_result is None:
            self.out.warn(f"L{line.number}: ASSERT_STDERR_CONTAINS: No previous SHELL command")
            return

        pattern = args.strip().strip('"\'')
        stderr = self._last_shell_result.get("stderr", "")

        if pattern in stderr:
            self.out.step("  ✅", f'ASSERT_STDERR_CONTAINS "{pattern}"')
            self.results.append(StepResult(
                name=f'ASSERT_STDERR "{pattern}"', status=StepStatus.PASSED
            ))
        else:
            self.out.step("  ❌", f'ASSERT_STDERR_CONTAINS "{pattern}"')
            self.errors.append(f'L{line.number}: Pattern "{pattern}" not found in stderr')
            self.results.append(StepResult(
                name=f'ASSERT_STDERR "{pattern}"',
                status=StepStatus.FAILED,
                message=f'Pattern "{pattern}" not found',
            ))
