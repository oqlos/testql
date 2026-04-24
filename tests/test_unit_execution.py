"""Tests for unit test execution mixin (testql.interpreter._unit)."""

from __future__ import annotations

import pytest
from pathlib import Path

from testql.interpreter import IqlInterpreter


class TestUnitExecution:
    """Test UNIT_PYTEST, UNIT_IMPORT, UNIT_ASSERT commands."""

    @pytest.fixture
    def interpreter(self):
        """Create IqlInterpreter with unit capabilities."""
        return IqlInterpreter(
            api_url="http://localhost:8101",
            quiet=True,
        )

    def test_unit_import_success(self, interpreter):
        """Test UNIT_IMPORT with existing module."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_IMPORT", args='"math"', raw='UNIT_IMPORT "math"')
        interpreter._cmd_unit_import(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_unit_import_failure(self, interpreter):
        """Test UNIT_IMPORT with non-existent module."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_IMPORT", args='"nonexistent_module_xyz"', raw='UNIT_IMPORT "nonexistent_module_xyz"')
        interpreter._cmd_unit_import(line.args, line)

        assert interpreter.results[-1].status.value == "failed"

    def test_unit_assert_success(self, interpreter):
        """Test UNIT_ASSERT with matching result."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_ASSERT", args='"len" "[[1,2,3]]" "3"', raw='UNIT_ASSERT "len" "[[1,2,3]]" "3"')
        interpreter._cmd_unit_assert(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_unit_assert_failure(self, interpreter):
        """Test UNIT_ASSERT with non-matching result."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_ASSERT", args='"len" "[[1,2,3]]" "99"', raw='UNIT_ASSERT "len" "[[1,2,3]]" "99"')
        interpreter._cmd_unit_assert(line.args, line)

        assert interpreter.results[-1].status.value == "failed"

    def test_unit_assert_builtin_function(self, interpreter):
        """Test UNIT_ASSERT with builtin function (abs)."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_ASSERT", args='"abs" "[-5]" "5"', raw='UNIT_ASSERT "abs" "[-5]" "5"')
        interpreter._cmd_unit_assert(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_unit_pytest_no_args(self, interpreter):
        """Test UNIT_PYTEST with no arguments."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_PYTEST", args='', raw='UNIT_PYTEST')
        interpreter._cmd_unit_pytest(line.args, line)

        # Should fail with error message
        assert any("requires path argument" in line for line in interpreter.out.lines)

    def test_unit_pytest_dry_run(self, interpreter):
        """Test UNIT_PYTEST in dry-run mode."""
        interpreter.dry_run = True
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_PYTEST", args='"tests/test_shell_execution.py"', raw='UNIT_PYTEST "tests/test_shell_execution.py"')
        interpreter._cmd_unit_pytest(line.args, line)

        assert interpreter._last_unit_result["dry_run"] is True
        assert interpreter.results[-1].status.value == "passed"


class TestUnitDryRun:
    """Test unit commands in dry-run mode."""

    @pytest.fixture
    def interpreter(self):
        return IqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)

    def test_unit_import_dry_run(self, interpreter):
        """Test UNIT_IMPORT in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_IMPORT", args='"some_module"', raw='UNIT_IMPORT "some_module"')
        interpreter._cmd_unit_import(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_unit_pytest_discover_dry_run(self, interpreter):
        """Test UNIT_PYTEST_DISCOVER in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNIT_PYTEST_DISCOVER", args='"tests/"', raw='UNIT_PYTEST_DISCOVER "tests/"')
        interpreter._cmd_unit_pytest_discover(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
