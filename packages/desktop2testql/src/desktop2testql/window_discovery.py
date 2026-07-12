"""Shared desktop window discovery for capture, vision, and automation."""

from __future__ import annotations

import os
from typing import Any

_JUNK_TITLES = frozenset(
    {
        "",
        "mutter guard window",
        "focusproxy",
        "content window",
    },
)
_JUNK_LABELS = frozenset({"mutter guard window", "focusproxy", "(unknown)"})
_JUNK_MARKERS = ("mutter guard", "focusproxy", "sun-awt-x11-xcanvaspeer", "javaawtcanvas")
_SKIP_TYPES = frozenset({"root", "helper"})
_MIN_CAPTURE_WIDTH = 80
_MIN_CAPTURE_HEIGHT = 60


def _display() -> str:
    if _vdisplay_available():
        from vdisplay.discovery import resolve_host_display

        return resolve_host_display(os.environ.get("DISPLAY"))
    return os.environ.get("DISPLAY", ":0").strip() or ":0"


def _vdisplay_available() -> bool:
    try:
        import vdisplay  # noqa: F401

        return True
    except ImportError:
        return False


def window_to_hex_id(window_id: str | int) -> str:
    raw = str(window_id).strip()
    if raw.lower().startswith("0x"):
        return raw
    return f"0x{int(raw):x}"


def _has_unusable_title(title: str, app_label: str) -> bool:
    return title in _JUNK_TITLES and (not app_label or app_label == "(unknown)")


def _is_internal_without_title(window: dict[str, Any], title: str, app_label: str) -> bool:
    return bool(not title and app_label in _JUNK_LABELS and window.get("is_internal"))


def _matches_junk_marker(title: str, wm_class: str) -> bool:
    return any(marker in wm_class or marker in title for marker in _JUNK_MARKERS)


def _meets_min_size(width: int, height: int) -> bool:
    return width >= _MIN_CAPTURE_WIDTH and height >= _MIN_CAPTURE_HEIGHT


def is_capture_window(window: dict[str, Any]) -> bool:
    """True when a window should be mirrored onto a monitor canvas."""
    if str(window.get("type") or "").lower() in _SKIP_TYPES:
        return False

    title = str(window.get("title") or window.get("name") or "").strip().lower()
    app_label = str(window.get("app_label") or "").strip().lower()
    if _has_unusable_title(title, app_label):
        return False
    if _is_internal_without_title(window, title, app_label):
        return False

    wm_class = str(window.get("wm_class") or "").lower()
    if _matches_junk_marker(title, wm_class):
        return False

    return _meets_min_size(int(window.get("width") or 0), int(window.get("height") or 0))


def _filter_capture_windows(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [window for window in raw if is_capture_window(window)]


def _fetch_vdisplay_windows(display: str, *, apps_only: bool) -> list[dict[str, Any]]:
    from vdisplay.discovery import list_windows

    return list_windows(display, apps_only=apps_only)


def list_capture_windows(*, display: str | None = None) -> list[dict[str, Any]]:
    """List windows suitable for monitor capture (apps first, then filtered fallback)."""
    if not _vdisplay_available():
        return []

    disp = display or _display()
    strict = [dict(item) for item in _fetch_vdisplay_windows(disp, apps_only=True)]
    if strict:
        return _filter_capture_windows(strict)

    broad = [dict(item) for item in _fetch_vdisplay_windows(disp, apps_only=False)]
    return _filter_capture_windows(broad)


def window_display_title(window: dict[str, Any]) -> str:
    title = str(window.get("title") or window.get("name") or "").strip()
    if title:
        return title
    app_label = str(window.get("app_label") or "").strip()
    if app_label and app_label != "(unknown)":
        return app_label
    wid = window.get("window_id")
    if wid is not None:
        return f"window-{window_to_hex_id(wid)}"
    return "window-unknown"


def window_matches(window: dict[str, Any], needle: str) -> bool:
    needle_l = needle.strip().lower()
    if not needle_l:
        return False

    fields = (
        window.get("title"),
        window.get("name"),
        window.get("app_label"),
        window.get("process_name"),
        window.get("wm_class"),
        window_display_title(window),
    )
    for value in fields:
        if needle_l in str(value or "").lower():
            return True

    wid = str(window.get("window_id") or "").lower()
    return bool(wid and (needle_l in wid or needle_l in f"window-{wid}"))
