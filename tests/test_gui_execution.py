"""Tests for GUI test execution mixin (testql.interpreter._gui)."""

from __future__ import annotations

import pytest

from testql.interpreter import IqlInterpreter


class TestGuiExecution:
    """Test GUI commands in dry-run mode (full tests require Playwright/Selenium)."""

    @pytest.fixture
    def interpreter(self):
        """Create IqlInterpreter with GUI capabilities in dry-run mode."""
        return IqlInterpreter(
            api_url="http://localhost:8101",
            quiet=True,
            dry_run=True,  # Dry-run to avoid needing Playwright/Selenium
        )

    def test_gui_start_dry_run(self, interpreter):
        """Test GUI_START in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_START", args='"http://localhost:5173"', raw='GUI_START "http://localhost:5173"')
        interpreter._cmd_gui_start(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_click_dry_run(self, interpreter):
        """Test GUI_CLICK in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_CLICK", args='"[data-testid=button]"', raw='GUI_CLICK "[data-testid=button]"')
        interpreter._cmd_gui_click(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_input_dry_run(self, interpreter):
        """Test GUI_INPUT in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_INPUT", args='"[data-testid=input]" "test text"', raw='GUI_INPUT "[data-testid=input]" "test text"')
        interpreter._cmd_gui_input(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_assert_visible_dry_run(self, interpreter):
        """Test GUI_ASSERT_VISIBLE in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_ASSERT_VISIBLE", args='"[data-testid=result]"', raw='GUI_ASSERT_VISIBLE "[data-testid=result]"')
        interpreter._cmd_gui_assert_visible(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_assert_text_dry_run(self, interpreter):
        """Test GUI_ASSERT_TEXT in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_ASSERT_TEXT", args='"[data-testid=result]" "expected"', raw='GUI_ASSERT_TEXT "[data-testid=result]" "expected"')
        interpreter._cmd_gui_assert_text(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_capture_dry_run(self, interpreter):
        """Test GUI_CAPTURE in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_CAPTURE", args='"[data-testid=main]" "screenshot.png"', raw='GUI_CAPTURE "[data-testid=main]" "screenshot.png"')
        interpreter._cmd_gui_capture(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_stop_dry_run(self, interpreter):
        """Test GUI_STOP in dry-run mode."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_STOP", args='', raw='GUI_STOP')
        interpreter._cmd_gui_stop(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_click_no_session_error(self, interpreter):
        """Test GUI_CLICK without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_CLICK", args='"[data-testid=button]"', raw='GUI_CLICK "[data-testid=button]"')
        interpreter._cmd_gui_click(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_start_no_args_error(self, interpreter):
        """Test GUI_START without arguments."""
        interpreter.dry_run = False
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="GUI_START", args='', raw='GUI_START')
        interpreter._cmd_gui_start(line.args, line)

        assert any("requires path or URL" in line for line in interpreter.out.lines)


class TestGuiDriverSelection:
    """Test GUI driver selection and initialization."""

    @pytest.fixture
    def interpreter(self):
        return IqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)

    def test_gui_driver_default_playwright(self, interpreter, monkeypatch):
        """Test default driver is playwright."""
        assert interpreter._gui_driver is None
        interpreter.vars.set("gui_driver", "playwright")
        # Mock playwright import to simulate it not being installed
        import sys
        monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
        assert interpreter._init_gui_driver() is False  # Returns False if not installed (dry-run)

    def test_gui_driver_selenium_fallback(self, interpreter, monkeypatch):
        """Test selenium driver selection."""
        interpreter.vars.set("gui_driver", "selenium")
        # Mock selenium import to simulate it not being installed
        import sys
        monkeypatch.setitem(sys.modules, "selenium", None)
        assert interpreter._init_gui_driver() is False  # Returns False if not installed (dry-run)
