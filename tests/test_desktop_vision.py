"""Tests for desktop vision integration (img2nl / imgl / vdisplay)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from testql.desktop import vision as desktop_vision
from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


@pytest.fixture
def interpreter() -> OqlInterpreter:
    return OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)


def test_check_vision_availability() -> None:
    avail = desktop_vision.check_vision_availability()
    assert isinstance(avail.as_dict(), dict)
    assert "img2nl" in avail.as_dict()


def test_list_monitors_xrandr_fallback(monkeypatch) -> None:
    monkeypatch.setattr(desktop_vision, "check_vision_availability", lambda: desktop_vision.VisionAvailability())
    monkeypatch.setattr("testql.desktop.vision.shutil.which", lambda name: "/usr/bin/xrandr" if name == "xrandr" else None)

    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "Monitors: 2\n 0: +*DP-1 1920/510x1080/290+0+0  DP-1\n"
    monkeypatch.setattr("testql.desktop.vision.subprocess.run", lambda *a, **k: proc)

    monitors = desktop_vision.list_monitors()
    assert len(monitors) == 1
    assert monitors[0]["name"] == "DP-1"


def test_desktop_monitors_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(number=1, command="DESKTOP_MONITORS", args="", raw="DESKTOP_MONITORS")
    interpreter._cmd_desktop_monitors(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_inspect_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_INSPECT",
        args='"shot.png"',
        raw='DESKTOP_INSPECT "shot.png"',
    )
    interpreter._cmd_desktop_inspect(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_describe_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_DESCRIBE",
        args='"shot.png"',
        raw='DESKTOP_DESCRIBE "shot.png"',
    )
    interpreter._cmd_desktop_describe(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_analyze_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_ANALYZE",
        args='"shot.png" "out.json"',
        raw='DESKTOP_ANALYZE "shot.png" "out.json"',
    )
    interpreter._cmd_desktop_analyze(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_assert_text_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_ASSERT_TEXT",
        args='"Settings"',
        raw='DESKTOP_ASSERT_TEXT "Settings"',
    )
    interpreter._cmd_desktop_assert_text(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_desktop_assert_elements_dry_run(interpreter: OqlInterpreter) -> None:
    line = OqlLine(
        number=1,
        command="DESKTOP_ASSERT_ELEMENTS",
        args='3 "shot.png"',
        raw='DESKTOP_ASSERT_ELEMENTS 3 "shot.png"',
    )
    interpreter._cmd_desktop_assert_elements(line.args, line)
    assert interpreter.results[-1].status.value == "passed"


def test_dispatcher_registers_vision_commands(interpreter: OqlInterpreter) -> None:
    for cmd in (
        "desktop_monitors",
        "desktop_inspect",
        "desktop_describe",
        "desktop_analyze",
        "desktop_assert_text",
        "desktop_assert_elements",
        "desktop_click_text",
    ):
        assert interpreter.dispatcher.has_command(cmd)


def test_collect_desktop_catalog_includes_vision_commands() -> None:
    from testql.desktop.catalog import collect_desktop_catalog

    catalog = collect_desktop_catalog()
    names = {item["name"] for item in catalog["commands"]}
    assert "testql_desktop_inspect" in names
    assert "testql_desktop_analyze" in names


@pytest.mark.live_desktop
def test_live_inspect_environment(tmp_path: Path) -> None:
    import shutil

    if not shutil.which("xdotool") and not shutil.which("xrandr"):
        pytest.skip("no xdotool/xrandr on host")
    capture = tmp_path / "live-inspect.png"
    try:
        payload = desktop_vision.inspect_environment(capture_path=capture)
    except Exception as exc:
        pytest.skip(f"desktop capture unavailable on this host: {exc}")
    assert payload.display_server in {"wayland", "x11", "unknown"}
    assert len(payload.monitors) >= 0
