"""Regression test: testql CLI must never block waiting for user input.

Root cause: check_and_upgrade() called input() when a newer version was
available on PyPI. Since Cascade/MCP/CI all get a TTY, this froze every
subsequent run_command in the session.

Fix: input() removed entirely. Version hint goes to stderr only.
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from testql import cli as cli_module
from testql.cli import _fetch_latest_version, check_and_upgrade, cli, main


CLI_PY = Path(cli_module.__file__)


class TestNoInputCall:
    """Static guarantee: input() must not appear in cli.py."""

    def test_no_input_in_source(self):
        source = CLI_PY.read_text()
        tree = ast.parse(source)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ]
        assert calls == [], (
            f"Found input() call(s) in cli.py at lines: "
            f"{[c.lineno for c in calls]}"
        )

    def test_no_subprocess_in_check_and_upgrade(self):
        source = inspect.getsource(check_and_upgrade)
        assert "subprocess" not in source
        assert "input(" not in source
        assert "os.execv" not in source


class TestCheckAndUpgradeNeverBlocks:
    """check_and_upgrade must return quickly regardless of TTY or version."""

    def test_runs_when_up_to_date(self):
        with patch.object(cli_module, "_fetch_latest_version", return_value="1.2.33"):
            with patch.object(cli_module, "pkg_version", return_value="1.2.33"):
                check_and_upgrade()  # must not raise or block

    def test_runs_when_outdated(self, capsys):
        with patch.object(cli_module, "_fetch_latest_version", return_value="9.9.9"):
            with patch.object(cli_module, "pkg_version", return_value="1.0.0"):
                check_and_upgrade()
        captured = capsys.readouterr()
        assert "9.9.9" in captured.err
        assert "pip install" in captured.err
        assert captured.out == ""  # nothing on stdout

    def test_runs_when_pypi_unreachable(self):
        with patch.object(cli_module, "_fetch_latest_version", return_value=None):
            check_and_upgrade()  # must not raise

    def test_runs_when_version_unavailable(self):
        with patch.object(cli_module, "pkg_version", side_effect=Exception("no dist")):
            check_and_upgrade()  # must not raise

    def test_is_tty_agnostic(self):
        """check_and_upgrade must work the same whether stdout is TTY or not."""
        with patch.object(cli_module, "_fetch_latest_version", return_value=None):
            with patch.object(sys.stdout, "isatty", return_value=True):
                check_and_upgrade()
            with patch.object(sys.stdout, "isatty", return_value=False):
                check_and_upgrade()


class TestMainNeverBlocks:
    """main() entry point must not block in any environment."""

    def test_main_via_runner(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "testql" in result.output.lower()

    def test_main_does_not_call_input(self):
        """Patch input() to raise — main() must never trigger it."""
        def _raise(*_):
            raise AssertionError("input() was called — this blocks the terminal!")

        runner = CliRunner()
        with patch("builtins.input", _raise):
            with patch.object(cli_module, "_fetch_latest_version", return_value="9.9.9"):
                result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
