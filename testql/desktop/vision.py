"""Vision layer for desktop E2E — img2nl, imgl, vdisplay (optional)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VisionAvailability:
    img2nl: bool = False
    imgl: bool = False
    vdisplay: bool = False
    tesseract: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "img2nl": self.img2nl,
            "imgl": self.imgl,
            "vdisplay": self.vdisplay,
            "tesseract": self.tesseract,
        }


def check_vision_availability() -> VisionAvailability:
    avail = VisionAvailability(tesseract=bool(shutil.which("tesseract")))
    try:
        import img2nl  # noqa: F401

        avail.img2nl = True
    except ImportError:
        pass
    try:
        import imgl  # noqa: F401

        avail.imgl = True
    except ImportError:
        pass
    try:
        import vdisplay  # noqa: F401

        avail.vdisplay = True
    except ImportError:
        pass
    return avail


def _display() -> str:
    return os.environ.get("IMGL_DISPLAY", os.environ.get("DISPLAY", ":0")).strip() or ":0"


def list_monitors() -> list[dict[str, Any]]:
    """List connected monitors via vdisplay or xrandr."""
    if check_vision_availability().vdisplay:
        from vdisplay.discovery import list_monitors as _list

        return [dict(item) for item in _list(_display())]

    if not shutil.which("xrandr"):
        return []

    proc = subprocess.run(
        ["xrandr", "--listmonitors"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "DISPLAY": _display()},
    )
    if proc.returncode != 0:
        return []

    monitors: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        primary = line.startswith("0:")
        match = re.search(
            r"(\d+):\s+\+?\*?(\S+)\s+(\d+)/\d+x(\d+)/\d+\+(\d+)\+(\d+)",
            line,
        )
        if not match:
            continue
        idx, name, width, height, x, y = match.groups()
        monitors.append(
            {
                "monitor_index": int(idx),
                "name": name,
                "primary": primary,
                "width": int(width),
                "height": int(height),
                "x": int(x),
                "y": int(y),
                "geometry": f"{width}x{height}+{x}+{y}",
            },
        )
    return monitors


def list_os_windows(*, apps_only: bool = True) -> list[dict[str, Any]]:
    """List OS windows via vdisplay or xdotool."""
    if check_vision_availability().vdisplay:
        from testql.desktop.window_discovery import list_capture_windows, window_display_title

        windows = list_capture_windows(display=_display())
        if apps_only:
            return windows
        return [
            {
                **window,
                "title": window_display_title(window),
            }
            for window in windows
        ]

    if not shutil.which("xdotool"):
        return []

    proc = subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--name", ""],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "DISPLAY": _display()},
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []

    windows: list[dict[str, Any]] = []
    for raw_id in proc.stdout.split():
        wid = raw_id.strip()
        if not wid.isdigit():
            continue
        title_proc = subprocess.run(
            ["xdotool", "getwindowname", wid],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "DISPLAY": _display()},
        )
        title = title_proc.stdout.strip() if title_proc.returncode == 0 else ""
        if apps_only and not title:
            continue
        windows.append(
            {
                "window_id": f"0x{int(wid):x}",
                "title": title or f"window-{wid}",
                "app_label": title.split(" - ")[0] if title else "",
            },
        )
    return windows


def describe_image(path: str | Path, *, locale: str = "pl") -> dict[str, Any]:
    """Heuristic image summary via img2nl."""
    image = Path(path).expanduser()
    if not image.is_file():
        return {"ok": False, "error": f"image not found: {image}"}

    if not check_vision_availability().img2nl:
        return {
            "ok": False,
            "error": "img2nl not installed — pip install -e ~/github/wronai/img2nl[analyze]",
        }

    from img2nl import analyze_image

    result = analyze_image(image, skip_thumbnail=True, locale=locale)
    scene = (result.features or {}).get("scene", {})
    return {
        "ok": result.ok,
        "path": str(image),
        "text": result.text,
        "scene_class": scene.get("scene_class"),
        "llm_hint": result.llm_hint,
        "width": result.width,
        "height": result.height,
        "error": result.error,
    }


def analyze_layout(path: str | Path, *, lang: str = "eng+pol") -> dict[str, Any]:
    """Semantic UI layout via imgl."""
    image = Path(path).expanduser()
    if not image.is_file():
        return {"ok": False, "error": f"image not found: {image}"}

    if not check_vision_availability().imgl:
        return {
            "ok": False,
            "error": "imgl not installed — pip install -e ~/github/semcod/imgl",
        }

    from imgl import analyze, scene_to_json
    from imgl.window_scope import discover_windows, summarize_windows

    try:
        scene = analyze(str(image), lang=lang)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "path": str(image)}

    summaries = summarize_windows(scene, image_path=str(image))
    windows = discover_windows(scene)
    texts = _collect_ocr_text(scene)
    element_count = int(scene.metadata.get("element_count") or 0)
    if not element_count:
        element_count = sum(len(window.elements) for window in scene.windows) + len(scene.orphan_elements)
    return {
        "ok": True,
        "path": str(image),
        "width": scene.width,
        "height": scene.height,
        "window_count": len(windows),
        "element_count": element_count,
        "windows": [
            {
                "id": item.window.id,
                "title": item.window.title or item.window.id,
                "elements": item.element_count,
                "interactive": item.interactive_count,
            }
            for item in summaries
        ],
        "text_samples": texts[:40],
        "scene_json": json.loads(scene_to_json(scene)),
    }


def _collect_ocr_text(scene: Any) -> list[str]:
    texts: list[str] = []
    for window in scene.windows:
        for element in window.elements:
            if element.text and element.text.strip():
                texts.append(element.text.strip())
    for element in getattr(scene, "orphan_elements", []) or []:
        if element.text and element.text.strip():
            texts.append(element.text.strip())
    return texts


def find_text(path: str | Path, needle: str, *, window: str | None = None) -> dict[str, Any]:
    """Find UI element containing text (imgl SceneActions)."""
    image = Path(path).expanduser()
    if not image.is_file():
        return {"ok": False, "error": f"image not found: {image}"}

    if not check_vision_availability().imgl:
        return {"ok": False, "error": "imgl not installed"}

    from imgl import analyze
    from imgl.actions import SceneActions

    try:
        scene = analyze(str(image))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    actions = SceneActions(scene)
    matches = list(actions.find(text=needle, window=window))
    if not matches:
        matches = list(actions.find(label=needle, window=window))
    if not matches:
        haystack = " ".join(_collect_ocr_text(scene)).lower()
        if needle.lower() in haystack:
            return {"ok": True, "found": True, "match_type": "ocr_haystack", "coords": None}
        return {"ok": True, "found": False, "needle": needle}

    target = matches[0]
    x, y = target.click_coords()
    return {
        "ok": True,
        "found": True,
        "match_type": "element",
        "needle": needle,
        "coords": {"x": x, "y": y},
        "element_type": target.element.type,
        "element_text": target.element.text,
        "window_id": target.window.id if target.window else None,
    }


@dataclass
class EnvironmentInspect:
    display_server: str
    display: str
    host_tools: list[str] = field(default_factory=list)
    vision: dict[str, bool] = field(default_factory=dict)
    monitors: list[dict[str, Any]] = field(default_factory=list)
    windows: list[dict[str, Any]] = field(default_factory=list)
    capture_path: str | None = None
    describe: dict[str, Any] | None = None
    layout: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "display_server": self.display_server,
            "display": self.display,
            "host_tools": self.host_tools,
            "vision": self.vision,
            "monitors": self.monitors,
            "windows": self.windows,
            "capture_path": self.capture_path,
            "describe": self.describe,
            "layout": self.layout,
        }


def inspect_environment(
    *,
    capture_path: str | Path | None = None,
    locale: str = "pl",
    lang: str = "eng+pol",
) -> EnvironmentInspect:
    """Full desktop discovery: monitors, windows, optional capture + vision."""
    from testql.desktop.backend import detect_display_server

    host_tools = [
        name
        for name in (
            "wmctrl",
            "xdotool",
            "wtype",
            "ydotool",
            "grim",
            "gnome-screenshot",
            "scrot",
            "xrandr",
            "tesseract",
        )
        if shutil.which(name)
    ]
    result = EnvironmentInspect(
        display_server=detect_display_server(),
        display=_display(),
        host_tools=host_tools,
        vision=check_vision_availability().as_dict(),
        monitors=list_monitors(),
        windows=list_os_windows(apps_only=True),
    )

    if capture_path is not None:
        path = Path(capture_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        from testql.desktop.vdisplay_capture import capture_via_vdisplay, save_capture_with_meta

        capture = capture_via_vdisplay(path)
        if not capture.ok:
            from testql.desktop.backend import get_desktop_backend

            get_desktop_backend().screenshot(str(path))
        else:
            save_capture_with_meta(path, capture)
        result.capture_path = str(path)
        result.describe = describe_image(path, locale=locale)
        result.layout = analyze_layout(path, lang=lang)

    return result
