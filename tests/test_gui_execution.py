"""Tests for GUI test execution mixin (testql.interpreter._gui)."""

from __future__ import annotations

import pytest

from testql.interpreter import OqlInterpreter


class TestGuiExecution:
    """Test GUI commands in dry-run mode (full tests require Playwright/Selenium)."""

    @pytest.fixture
    def interpreter(self):
        """Create OqlInterpreter with GUI capabilities in dry-run mode."""
        return OqlInterpreter(
            api_url="http://localhost:8101",
            quiet=True,
            dry_run=True,  # Dry-run to avoid needing Playwright/Selenium
        )

    def test_gui_start_dry_run(self, interpreter):
        """Test GUI_START in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_START", args='"http://localhost:5173"', raw='GUI_START "http://localhost:5173"')
        interpreter._cmd_gui_start(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_click_dry_run(self, interpreter):
        """Test GUI_CLICK in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_CLICK", args='"[data-testid=button]"', raw='GUI_CLICK "[data-testid=button]"')
        interpreter._cmd_gui_click(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_input_dry_run(self, interpreter):
        """Test GUI_INPUT in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_INPUT", args='"[data-testid=input]" "test text"', raw='GUI_INPUT "[data-testid=input]" "test text"')
        interpreter._cmd_gui_input(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_scroll_dry_run(self, interpreter):
        """Test GUI_SCROLL in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_SCROLL", args='".module-main-content" y=900', raw='GUI_SCROLL ".module-main-content" y=900')
        interpreter._cmd_gui_scroll(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_SCROLL ".module-main-content"' in interpreter.results[-1].name

    def test_gui_assert_visible_dry_run(self, interpreter):
        """Test GUI_ASSERT_VISIBLE in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_VISIBLE", args='"[data-testid=result]"', raw='GUI_ASSERT_VISIBLE "[data-testid=result]"')
        interpreter._cmd_gui_assert_visible(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_assert_text_dry_run(self, interpreter):
        """Test GUI_ASSERT_TEXT in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_TEXT", args='"[data-testid=result]" "expected"', raw='GUI_ASSERT_TEXT "[data-testid=result]" "expected"')
        interpreter._cmd_gui_assert_text(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_eval_dry_run(self, interpreter):
        """Test GUI_EVAL in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_EVAL", args='"return location.href"', raw='GUI_EVAL "return location.href"')
        interpreter._cmd_gui_eval(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_EVAL "return location.href"' in interpreter.results[-1].name

    def test_gui_assert_count_dry_run(self, interpreter):
        """Test GUI_ASSERT_COUNT in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_COUNT", args='".task" == 12', raw='GUI_ASSERT_COUNT ".task" == 12')
        interpreter._cmd_gui_assert_count(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_ASSERT_COUNT ".task" == 12' in interpreter.results[-1].name

    def test_gui_wait_for_count_dry_run(self, interpreter):
        """Test GUI_WAIT_FOR_COUNT in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_WAIT_FOR_COUNT", args='".task" >= 2 3000', raw='GUI_WAIT_FOR_COUNT ".task" >= 2 3000')
        interpreter._cmd_gui_wait_for_count(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_WAIT_FOR_COUNT ".task" >= 2' in interpreter.results[-1].name

    def test_gui_assert_url_param_dry_run(self, interpreter):
        """Test GUI_ASSERT_URL_PARAM in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_URL_PARAM", args='"type" "36m"', raw='GUI_ASSERT_URL_PARAM "type" "36m"')
        interpreter._cmd_gui_assert_url_param(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_ASSERT_URL_PARAM "type" == "36m"' in interpreter.results[-1].name

    def test_gui_assert_value_dry_run(self, interpreter):
        """Test GUI_ASSERT_VALUE in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_VALUE", args='"#filter-kind-select" "36m"', raw='GUI_ASSERT_VALUE "#filter-kind-select" "36m"')
        interpreter._cmd_gui_assert_value(line.args, line)

        assert interpreter.results[-1].status.value == "passed"
        assert 'GUI_ASSERT_VALUE "#filter-kind-select" == "36m"' in interpreter.results[-1].name

    def test_gui_capture_dry_run(self, interpreter):
        """Test GUI_CAPTURE in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_CAPTURE", args='"[data-testid=main]" "screenshot.png"', raw='GUI_CAPTURE "[data-testid=main]" "screenshot.png"')
        interpreter._cmd_gui_capture(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_stop_dry_run(self, interpreter):
        """Test GUI_STOP in dry-run mode."""
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_STOP", args='', raw='GUI_STOP')
        interpreter._cmd_gui_stop(line.args, line)

        assert interpreter.results[-1].status.value == "passed"

    def test_gui_click_no_session_error(self, interpreter):
        """Test GUI_CLICK without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_CLICK", args='"[data-testid=button]"', raw='GUI_CLICK "[data-testid=button]"')
        interpreter._cmd_gui_click(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_scroll_no_session_error(self, interpreter):
        """Test GUI_SCROLL without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_SCROLL", args='".module-main-content" 900', raw='GUI_SCROLL ".module-main-content" 900')
        interpreter._cmd_gui_scroll(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_assert_count_no_session_error(self, interpreter):
        """Test GUI_ASSERT_COUNT without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_COUNT", args='".task" 12', raw='GUI_ASSERT_COUNT ".task" 12')
        interpreter._cmd_gui_assert_count(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_wait_for_count_no_session_error(self, interpreter):
        """Test GUI_WAIT_FOR_COUNT without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_WAIT_FOR_COUNT", args='".task" 12', raw='GUI_WAIT_FOR_COUNT ".task" 12')
        interpreter._cmd_gui_wait_for_count(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_assert_url_param_no_session_error(self, interpreter):
        """Test GUI_ASSERT_URL_PARAM without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_URL_PARAM", args='"type" "36m"', raw='GUI_ASSERT_URL_PARAM "type" "36m"')
        interpreter._cmd_gui_assert_url_param(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_assert_value_no_session_error(self, interpreter):
        """Test GUI_ASSERT_VALUE without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_ASSERT_VALUE", args='"#filter-kind-select" "36m"', raw='GUI_ASSERT_VALUE "#filter-kind-select" "36m"')
        interpreter._cmd_gui_assert_value(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_eval_no_session_error(self, interpreter):
        """Test GUI_EVAL without active session (non-dry-run)."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_EVAL", args='"return 1"', raw='GUI_EVAL "return 1"')
        interpreter._cmd_gui_eval(line.args, line)

        assert interpreter.results[-1].status.value == "error"
        assert "No active GUI session" in interpreter.results[-1].message

    def test_gui_assert_count_comparison_helper(self, interpreter):
        """Test GUI_ASSERT_COUNT parser and comparison helpers."""
        assert interpreter._parse_count_assertion_args('".task" 12') == (".task", "==", 12)
        assert interpreter._parse_count_assertion_args('".task" >= 1') == (".task", ">=", 1)
        assert interpreter._parse_wait_count_args('".task" >= 1 7000') == (".task", ">=", 1, 7000)
        assert interpreter._parse_wait_count_args('".task" 12') == (".task", "==", 12, 5000)
        assert interpreter._parse_value_assertion_args('"#kind" "36m"') == ("#kind", "==", "36m")
        assert interpreter._parse_value_assertion_args('"#kind" != ""') == ("#kind", "!=", "")
        assert interpreter._compare_count(12, "==", 12) is True
        assert interpreter._compare_count(12, ">=", 10) is True
        assert interpreter._compare_count(12, "<", 10) is False
        assert interpreter._compare_value("36m", "==", "36m") is True
        assert interpreter._compare_value("36m", "!=", "6m") is True
        assert interpreter._compare_value("periodic-36m", "CONTAINS", "36m") is True

    def test_gui_network_error_helpers(self, interpreter):
        """Test transient browser network error detection."""
        assert interpreter._same_url_without_hash("http://x.test/a?b=1#top", "http://x.test/a?b=1") is True
        assert interpreter._is_transient_browser_network_error(Exception("TypeError: Failed to fetch")) is True
        assert interpreter._is_transient_browser_network_error(Exception("Page.goto: net::ERR_ABORTED")) is True
        assert interpreter._is_transient_browser_network_error(Exception("SyntaxError")) is False

    def test_gui_start_no_args_error(self, interpreter):
        """Test GUI_START without arguments."""
        interpreter.dry_run = False
        from testql.interpreter._parser import OqlLine

        line = OqlLine(number=1, command="GUI_START", args='', raw='GUI_START')
        interpreter._cmd_gui_start(line.args, line)

        assert any("requires path or URL" in line for line in interpreter.out.lines)


class TestGuiDriverSelection:
    """Test GUI driver selection and initialization."""

    @pytest.fixture
    def interpreter(self):
        return OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)

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
