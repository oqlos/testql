"""Tests for shell execution mixin (testql.interpreter._shell)."""

from __future__ import annotations

import pytest
from pathlib import Path

from testql.interpreter import IqlInterpreter


class TestShellExecution:
    """Test SHELL, EXEC, RUN commands and assertions."""

    @pytest.fixture
    def interpreter(self, tmp_path):
        """Create IqlInterpreter with shell capabilities."""
        return IqlInterpreter(
            api_url="http://localhost:8101",
            quiet=True,
        )

    def test_shell_echo_command(self, interpreter, tmp_path):
        """Test basic SHELL command execution."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SHELL", args='"echo hello world" 5000', raw='SHELL "echo hello world" 5000')
        interpreter._cmd_shell(line.args, line)

        assert interpreter._last_shell_result is not None
        assert interpreter._last_shell_result["returncode"] == 0
        assert "hello world" in interpreter._last_shell_result["stdout"]
        assert interpreter.results[-1].status.value == "passed"

    def test_shell_with_exit_code(self, interpreter):
        """Test SHELL command with non-zero exit code."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SHELL", args='"exit 42" 5000', raw='SHELL "exit 42" 5000')
        interpreter._cmd_shell(line.args, line)

        assert interpreter._last_shell_result["returncode"] == 42
        # Non-zero exit is WARNING, not ERROR
        assert interpreter.results[-1].status.value in ("passed", "warning")

    def test_assert_exit_code_success(self, interpreter):
        """Test ASSERT_EXIT_CODE with matching code."""
        from testql.interpreter._parser import IqlLine

        # First execute a command
        shell_line = IqlLine(number=1, command="SHELL", args='"echo test"', raw='SHELL "echo test"')
        interpreter._cmd_shell(shell_line.args, shell_line)

        # Then assert exit code
        assert_line = IqlLine(number=2, command="ASSERT_EXIT_CODE", args="0", raw="ASSERT_EXIT_CODE 0")
        interpreter._cmd_assert_exit_code(assert_line.args, assert_line)

        assert interpreter.results[-1].status.value == "passed"

    def test_assert_exit_code_failure(self, interpreter):
        """Test ASSERT_EXIT_CODE with non-matching code."""
        from testql.interpreter._parser import IqlLine

        shell_line = IqlLine(number=1, command="SHELL", args='"exit 1"', raw='SHELL "exit 1"')
        interpreter._cmd_shell(shell_line.args, shell_line)

        assert_line = IqlLine(number=2, command="ASSERT_EXIT_CODE", args="0", raw="ASSERT_EXIT_CODE 0")
        interpreter._cmd_assert_exit_code(assert_line.args, assert_line)

        assert interpreter.results[-1].status.value == "failed"
        assert len(interpreter.errors) == 1

    def test_assert_stdout_contains_success(self, interpreter):
        """Test ASSERT_STDOUT_CONTAINS finding pattern."""
        from testql.interpreter._parser import IqlLine

        shell_line = IqlLine(number=1, command="SHELL", args='"echo hello world"', raw='SHELL "echo hello world"')
        interpreter._cmd_shell(shell_line.args, shell_line)

        assert_line = IqlLine(number=2, command="ASSERT_STDOUT_CONTAINS", args='"hello"', raw='ASSERT_STDOUT_CONTAINS "hello"')
        interpreter._cmd_assert_stdout_contains(assert_line.args, assert_line)

        assert interpreter.results[-1].status.value == "passed"

    def test_assert_stdout_contains_failure(self, interpreter):
        """Test ASSERT_STDOUT_CONTAINS not finding pattern."""
        from testql.interpreter._parser import IqlLine

        shell_line = IqlLine(number=1, command="SHELL", args='"echo hello world"', raw='SHELL "echo hello world"')
        interpreter._cmd_shell(shell_line.args, shell_line)

        assert_line = IqlLine(number=2, command="ASSERT_STDOUT_CONTAINS", args='"goodbye"', raw='ASSERT_STDOUT_CONTAINS "goodbye"')
        interpreter._cmd_assert_stdout_contains(assert_line.args, assert_line)

        assert interpreter.results[-1].status.value == "failed"

    def test_shell_timeout(self, interpreter):
        """Test SHELL command timeout."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SHELL", args='"sleep 5" 100', raw='SHELL "sleep 5" 100')
        interpreter._cmd_shell(line.args, line)

        assert interpreter._last_shell_result.get("timeout") is True
        assert interpreter.results[-1].status.value == "error"

    def test_shell_no_previous_command_warning(self, interpreter):
        """Test assertion without previous SHELL command."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="ASSERT_EXIT_CODE", args="0", raw="ASSERT_EXIT_CODE 0")
        interpreter._cmd_assert_exit_code(line.args, line)

        # Should warn but not fail - check output lines contain warning
        assert any("ASSERT_EXIT_CODE" in line and "No previous" in line for line in interpreter.out.lines)


class TestShellDryRun:
    """Test shell commands in dry-run mode."""

    @pytest.fixture
    def interpreter(self):
        return IqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)

    def test_shell_dry_run(self, interpreter):
        """Test SHELL in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SHELL", args='"rm -rf /"', raw='SHELL "rm -rf /"')
        interpreter._cmd_shell(line.args, line)

        assert interpreter._last_shell_result["dry_run"] is True
        assert interpreter._last_shell_result["returncode"] == 0
        assert interpreter.results[-1].status.value == "passed"
