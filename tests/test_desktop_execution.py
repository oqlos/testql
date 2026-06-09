"""Dry-run tests for DESKTOP_* interpreter commands."""

from __future__ import annotations

import pytest

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


@pytest.fixture
def interpreter() -> OqlInterpreter:
    return OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)


def test_desktop_list_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(number=1, command="DESKTOP_LIST", args="", raw="DESKTOP_LIST")
    interpreter._cmd_desktop_list(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_focus_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_FOCUS",
        args='"Cursor"',
        raw='DESKTOP_FOCUS "Cursor"',
    )
    interpreter._cmd_desktop_focus(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_launch_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_LAUNCH",
        args='"/usr/bin/xterm"',
        raw='DESKTOP_LAUNCH "/usr/bin/xterm"',
    )
    interpreter._cmd_desktop_launch(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_click_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(number=1, command="DESKTOP_CLICK", args="100 200", raw="DESKTOP_CLICK 100 200")
    interpreter._cmd_desktop_click(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_type_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_TYPE",
        args='"hello desktop"',
        raw='DESKTOP_TYPE "hello desktop"',
    )
    interpreter._cmd_desktop_type(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_key_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(number=1, command="DESKTOP_KEY", args="Return", raw="DESKTOP_KEY Return")
    interpreter._cmd_desktop_key(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_capture_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_CAPTURE",
        args='"shot.png"',
        raw='DESKTOP_CAPTURE "shot.png"',
    )
    interpreter._cmd_desktop_capture(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_assert_window_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_ASSERT_WINDOW",
        args='"Cursor"',
        raw='DESKTOP_ASSERT_WINDOW "Cursor"',
    )
    interpreter._cmd_desktop_assert_window(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_dispatcher_registers_desktop_commands(interpreter: OqlInterpreter) -> None:
    for cmd in (
        "desktop_list",
        "desktop_focus",
        "desktop_launch",
        "desktop_click",
        "desktop_type",
        "desktop_key",
        "desktop_capture",
        "desktop_assert_window",
        "desktop_monitors",
        "desktop_inspect",
        "desktop_describe",
        "desktop_analyze",
        "desktop_assert_text",
        "desktop_assert_elements",
        "desktop_click_text",
        "desktop_stop",
    ):
        assert interpreter.dispatcher.has_command(cmd)
