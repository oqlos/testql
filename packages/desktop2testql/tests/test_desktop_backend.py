"""Unit tests for native desktop backend."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from desktop2testql.backend import LinuxDesktopBackend
from desktop2testql.wmctrl import parse_wmctrl_listing


WMCTRL_SAMPLE = """\
0x02800007  0 0    0 1920 1080 nvida Koru - testql
0x02800009  0 100  100 800 600 nvida Terminal
"""


def test_parse_wmctrl_listing() -> None:
    windows = parse_wmctrl_listing(WMCTRL_SAMPLE)
    assert len(windows) == 2
    assert windows[0].id == "0x02800007"
    assert "Koru" in windows[0].title
    assert windows[0].width == 1920


def test_focus_window_by_title(monkeypatch) -> None:
    backend = LinuxDesktopBackend()

    monkeypatch.setattr(
        "desktop2testql.backend.shutil.which",
        lambda name: "/usr/bin/" + name if name in {"wmctrl", "xdotool"} else None,
    )

    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        proc = MagicMock()
        proc.returncode = 0
        if argv[:3] == ["wmctrl", "-l", "-G"]:
            proc.stdout = WMCTRL_SAMPLE
        elif argv[:2] == ["xdotool", "getactivewindow"]:
            proc.stdout = "41943047\n"
        else:
            proc.stdout = ""
        proc.stderr = ""
        return proc

    monkeypatch.setattr("desktop2testql.backend._run", fake_run)
    monkeypatch.setattr(backend, "_list_windows_vdisplay", lambda: [])

    focused = backend.focus_window(title="Terminal")
    assert focused is not None
    assert focused.title == "Terminal"
    assert any(cmd[:3] == ["wmctrl", "-ia", "0x02800009"] for cmd in calls)


def test_launch_executable(tmp_path: Path, monkeypatch) -> None:
    script = tmp_path / "hello.sh"
    script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    script.chmod(0o755)

    backend = LinuxDesktopBackend()
    fake_proc = MagicMock()
    fake_proc.pid = 4242
    monkeypatch.setattr("desktop2testql.backend.subprocess.Popen", lambda *a, **k: fake_proc)

    pid = backend.launch(str(script), "--verbose")
    assert pid == 4242
    assert 4242 in backend.session.launched_pids


def test_type_text_wayland(monkeypatch) -> None:
    backend = LinuxDesktopBackend()
    monkeypatch.setattr("desktop2testql.backend.detect_display_server", lambda: "wayland")
    backend._display_server = "wayland"

    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        proc.stderr = ""
        return proc

    monkeypatch.setattr(
        "desktop2testql.backend.shutil.which",
        lambda name: "/usr/bin/wtype" if name == "wtype" else None,
    )
    monkeypatch.setattr("desktop2testql.backend._run", fake_run)

    backend.type_text("hello")
    assert calls == [["wtype", "hello"]]


def test_list_windows_xdotool_fallback(monkeypatch) -> None:
    backend = LinuxDesktopBackend()
    monkeypatch.setattr("desktop2testql.backend.shutil.which", lambda name: None)

    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        if name == "xdotool":
            return "/usr/bin/xdotool"
        return None

    monkeypatch.setattr("desktop2testql.backend.shutil.which", fake_which)

    def fake_run(argv, **kwargs):
        calls.append(argv)
        proc = MagicMock()
        proc.returncode = 0
        if argv[:3] == ["xdotool", "search", "--onlyvisible"]:
            proc.stdout = "12345\n"
        elif argv[:2] == ["xdotool", "getwindowname"]:
            proc.stdout = "Test Window\n"
        elif argv[:2] == ["xdotool", "getwindowgeometry"]:
            proc.stdout = "WINDOW=12345\nX=10\nY=20\nWIDTH=800\nHEIGHT=600\n"
        else:
            proc.stdout = ""
        proc.stderr = ""
        return proc

    monkeypatch.setattr("desktop2testql.backend._run", fake_run)
    monkeypatch.setattr(backend, "_list_windows_vdisplay", lambda: [])
    windows = backend.list_windows()
    assert len(windows) == 1
    assert windows[0].title == "Test Window"
    assert windows[0].id == "0x3039"


def test_screenshot_vdisplay_failure_does_not_raise(monkeypatch, tmp_path: Path) -> None:
    backend = LinuxDesktopBackend()
    out = tmp_path / "cap.png"

    def boom(*args, **kwargs):
        raise RuntimeError("xrandr missing")

    monkeypatch.setattr(
        "desktop2testql.vdisplay_capture.capture_via_vdisplay",
        boom,
    )
    assert backend._screenshot_vdisplay(out) is False


def test_screenshot_scrot_fallback_on_wayland(monkeypatch, tmp_path: Path) -> None:
    backend = LinuxDesktopBackend()
    monkeypatch.setattr("desktop2testql.backend.detect_display_server", lambda: "wayland")
    backend._display_server = "wayland"
    monkeypatch.setenv("DISPLAY", ":0")

    out = tmp_path / "cap.png"

    def fake_which(name: str) -> str | None:
        if name in {"grim", "gnome-screenshot", "scrot"}:
            return f"/usr/bin/{name}"
        return None

    monkeypatch.setattr("desktop2testql.backend.shutil.which", fake_which)
    monkeypatch.setattr(backend, "_screenshot_vdisplay", lambda path, monitor=None: False)
    monkeypatch.setattr(backend, "_screenshot_is_blank", lambda path: False)
    monkeypatch.setattr(backend, "_screenshot_mss", lambda path: False)

    def fake_run(argv, **kwargs):
        proc = MagicMock()
        if argv[0] == "grim":
            proc.returncode = 1
            proc.stderr = "wlr-screencopy unsupported"
        elif argv[0] == "gnome-screenshot":
            proc.returncode = 1
            proc.stderr = "gdk failed"
        elif argv[0] == "scrot":
            proc.returncode = 0
            out.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000)
        else:
            proc.returncode = 1
        proc.stdout = ""
        return proc

    monkeypatch.setattr("desktop2testql.backend._run", fake_run)
    backend.screenshot(str(out))
    assert out.is_file()


@pytest.mark.live_desktop
def test_live_list_windows() -> None:
    """Optional live probe when wmctrl or xdotool is installed."""
    import shutil

    if not shutil.which("wmctrl") and not shutil.which("xdotool"):
        pytest.skip("no wmctrl/xdotool on host")
    backend = LinuxDesktopBackend()
    windows = backend.list_windows()
    assert isinstance(windows, list)
