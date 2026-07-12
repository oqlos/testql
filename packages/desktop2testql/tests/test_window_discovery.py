"""Tests for shared desktop window discovery."""

from __future__ import annotations

from desktop2testql import window_discovery as wd


def test_is_capture_window_rejects_root_and_junk() -> None:
    assert wd.is_capture_window({"type": "root", "width": 4000, "height": 2000}) is False
    assert wd.is_capture_window({"type": "helper", "title": "mutter guard window", "width": 400, "height": 300}) is False
    assert wd.is_capture_window({"type": "application", "title": "Toolbox", "width": 800, "height": 600}) is True


def test_list_capture_windows_prefers_apps_only(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_list_windows(display, apps_only=False):
        calls.append(apps_only)
        if apps_only:
            return [{"window_id": "1", "type": "application", "title": "Toolbox", "width": 800, "height": 600}]
        return [
            {"window_id": "1", "type": "application", "title": "Toolbox", "width": 800, "height": 600},
            {"window_id": "2", "type": "root", "width": 4000, "height": 2000},
        ]

    monkeypatch.setattr(wd, "_vdisplay_available", lambda: True)
    monkeypatch.setattr(wd, "_fetch_vdisplay_windows", fake_list_windows)

    windows = wd.list_capture_windows(display=":0")
    assert calls == [True]
    assert len(windows) == 1
    assert windows[0]["title"] == "Toolbox"


def test_list_capture_windows_falls_back_when_apps_empty(monkeypatch) -> None:
    def fake_list_windows(display, apps_only=False):
        if apps_only:
            return []
        return [
            {"window_id": "99", "type": "application", "title": "", "app_label": "MyApp", "width": 640, "height": 480},
            {"window_id": "2", "type": "root", "width": 4000, "height": 2000},
        ]

    monkeypatch.setattr(wd, "_vdisplay_available", lambda: True)
    monkeypatch.setattr(wd, "_fetch_vdisplay_windows", fake_list_windows)

    windows = wd.list_capture_windows(display=":0")
    assert len(windows) == 1
    assert windows[0]["app_label"] == "MyApp"


def test_window_matches_title_and_synthetic_id() -> None:
    window = {"window_id": "0xc00004", "title": "Toolbox", "width": 800, "height": 600}
    assert wd.window_matches(window, "toolbox")
    assert wd.window_matches(window, "0xc00004")
    assert wd.window_matches({"window_id": "913", "title": "", "width": 200, "height": 200}, "window-913")
