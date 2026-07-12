"""Tests for vdisplay composite screenshot capture."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from desktop2testql import vdisplay_capture as vc


def _enable_vdisplay_mocks(monkeypatch) -> None:
    monkeypatch.setattr(vc, "_VDISPLAY_AVAILABLE", True)
    monkeypatch.setattr(vc, "resolve_display", lambda: ":0")


def test_capture_monitor_composite_places_windows(monkeypatch, tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    _enable_vdisplay_mocks(monkeypatch)
    monkeypatch.setattr(vc, "shutil_which", lambda name: "/usr/bin/xwd" if name == "xwd" else None)
    monkeypatch.setattr(
        vc,
        "list_outputs",
        lambda display: [
            {
                "name": "DP-2",
                "primary": True,
                "monitor_id": 0,
                "x": 4096,
                "y": 0,
                "width": 100,
                "height": 80,
            },
        ],
    )
    monkeypatch.setattr(
        vc,
        "list_capture_windows",
        lambda display=None: [
            {
                "window_id": "8388615",
                "title": "Toolbox",
                "type": "application",
                "monitor_id": 0,
                "x": 4100,
                "y": 10,
                "width": 40,
                "height": 30,
            },
        ],
    )
    monkeypatch.setattr(vc, "is_blank_image", lambda path, **kw: False)

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (5, 5), color=(120, 80, 40)).save(buf, format="PNG")
    fake_png = buf.getvalue()
    monkeypatch.setattr(vc, "_xwd_window_png", lambda display, wid: fake_png)

    out = tmp_path / "cap.png"
    result = vc.capture_monitor_composite(out, monitor="primary")
    assert result.ok is True
    assert result.method == "vdisplay_composite"
    assert result.window_count == 1
    assert out.is_file()


def test_capture_via_vdisplay_prefers_mirror(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_mirror(path, **kwargs):
        calls.append("mirror")
        return vc.CaptureResult(ok=True, path=str(path), method="vdisplay_mirror_virtual")

    def fake_monitor(path, **kwargs):
        calls.append("monitor")
        return vc.CaptureResult(ok=False, path=str(path), error="skip")

    monkeypatch.setattr(vc, "capture_monitor_mirror_virtual", fake_mirror)
    monkeypatch.setattr(vc, "capture_monitor_composite", fake_monitor)

    out = tmp_path / "cap.png"
    result = vc.capture_via_vdisplay(out)
    assert result.ok is True
    assert result.method == "vdisplay_mirror_virtual"
    assert calls == ["mirror"]


def test_capture_desktop_composite_places_windows(monkeypatch, tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    _enable_vdisplay_mocks(monkeypatch)
    monkeypatch.setattr(
        vc,
        "list_outputs",
        lambda display: [
            {"name": "DP-1", "x": 0, "y": 0, "width": 100, "height": 80},
            {"name": "DP-2", "x": 100, "y": 0, "width": 50, "height": 40},
        ],
    )
    monkeypatch.setattr(
        vc,
        "list_capture_windows",
        lambda display=None: [
            {"window_id": "1", "x": 10, "y": 5, "width": 20, "height": 15},
        ],
    )
    monkeypatch.setattr(vc, "is_blank_image", lambda path, **kw: False)

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(10, 20, 30)).save(buf, format="PNG")
    monkeypatch.setattr(vc, "_xwd_window_png", lambda display, wid: buf.getvalue())

    out = tmp_path / "desktop.png"
    result = vc.capture_desktop_composite(out)
    assert result.ok is True
    assert result.method == "vdisplay_desktop_composite"
    assert result.window_count == 1
    assert result.width == 150
    assert result.height == 80


def test_capture_via_vdisplay_falls_back_to_scrot_region(monkeypatch, tmp_path: Path) -> None:
    _enable_vdisplay_mocks(monkeypatch)

    def fail_capture(path, **kwargs):
        return vc.CaptureResult(ok=False, path=str(path), error="skip")

    monkeypatch.setattr(vc, "capture_monitor_mirror_virtual", fail_capture)
    monkeypatch.setattr(vc, "capture_monitor_composite", fail_capture)
    monkeypatch.setattr(vc, "capture_desktop_composite", fail_capture)
    monkeypatch.setattr(
        vc,
        "list_outputs",
        lambda display: [{"name": "HDMI-1", "primary": True, "x": 0, "y": 0, "width": 80, "height": 60}],
    )
    monkeypatch.setattr(vc, "capture_display_png", lambda disp, region: b"\x89PNG" + b"\x00" * 2000)
    monkeypatch.setattr(vc, "is_blank_image", lambda path, **kw: False)

    out = tmp_path / "region.png"
    result = vc.capture_via_vdisplay(out, mirror_virtual=False)
    assert result.ok is True
    assert result.method == "vdisplay_scrot_region"
    assert result.monitor == "HDMI-1"


def test_capture_via_vdisplay_falls_back(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_mirror(path, **kwargs):
        calls.append("mirror")
        return vc.CaptureResult(ok=False, path=str(path), error="no xvfb")

    def fake_monitor(path, **kwargs):
        calls.append("monitor")
        return vc.CaptureResult(ok=False, path=str(path), error="no windows")

    def fake_desktop(path, **kwargs):
        calls.append("desktop")
        return vc.CaptureResult(ok=True, path=str(path), method="vdisplay_desktop_composite")

    monkeypatch.setattr(vc, "capture_monitor_mirror_virtual", fake_mirror)
    monkeypatch.setattr(vc, "capture_monitor_composite", fake_monitor)
    monkeypatch.setattr(vc, "capture_desktop_composite", fake_desktop)

    out = tmp_path / "cap.png"
    result = vc.capture_via_vdisplay(out)
    assert result.ok is True
    assert calls == ["mirror", "monitor", "desktop"]


def test_backend_uses_vdisplay_when_scrot_blank(monkeypatch, tmp_path: Path) -> None:
    from desktop2testql.backend import LinuxDesktopBackend

    backend = LinuxDesktopBackend()
    out = tmp_path / "shot.png"
    out.write_bytes(b"blank")

    monkeypatch.setattr(
        "desktop2testql.backend.shutil.which",
        lambda name: "/usr/bin/scrot" if name == "scrot" else None,
    )

    def fake_run(argv, **kwargs):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        proc.stderr = ""
        return proc

    monkeypatch.setattr("desktop2testql.backend._run", fake_run)
    monkeypatch.setattr(backend, "_screenshot_is_blank", lambda path: True)
    monkeypatch.setattr(backend, "_screenshot_mss", lambda path: False)

    captured: dict[str, object] = {}

    def fake_vdisplay(path, monitor=None):
        captured["path"] = path
        Path(path).write_bytes(b"\x89PNG" + b"\x00" * 2000)
        return True

    monkeypatch.setattr(backend, "_screenshot_vdisplay", fake_vdisplay)
    backend.screenshot(str(out))
    assert str(captured.get("path")) == str(out)
