"""vdisplay-based screenshot capture — obejście braku uprawnień Wayland.

Flow „mirror → vdisplay → screenshot”:
  1. vdisplay wykrywa okna na wybranym monitorze hosta
  2. xwd -id <window> kopiuje piksele okien (działa bez portalu GNOME)
  3. obraz składany na canvas o rozmiarze monitora
  4. canvas ląduje na wirtualnym Xvfb (VirtualDisplaySession / vdisplay virtual)
  5. zrzut z Xvfb przez xwd (bez uprawnień Wayland)

Na GNOME/Wayland scrot/grim/gnome-screenshot często zwracają czarny obraz roota.
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from desktop2testql.window_discovery import list_capture_windows

_VDISPLAY_IMPORT_ERROR: str | None = None

try:
    from vdisplay import VirtualDisplaySession
    from vdisplay.capture.linux_xwd import capture_display_png, xwd_bytes_to_png
    from vdisplay.discovery import list_outputs, resolve_host_display

    _VDISPLAY_AVAILABLE = True
except ImportError as exc:
    _VDISPLAY_AVAILABLE = False
    _VDISPLAY_IMPORT_ERROR = str(exc)

    def list_outputs(display):  # type: ignore[no-redef,misc]
        raise RuntimeError(_VDISPLAY_IMPORT_ERROR or "vdisplay not available")

    def resolve_host_display(display):  # type: ignore[no-redef,misc]
        raise RuntimeError(_VDISPLAY_IMPORT_ERROR or "vdisplay not available")

    def capture_display_png(display, region=None):  # type: ignore[no-redef,misc]
        raise RuntimeError(_VDISPLAY_IMPORT_ERROR or "vdisplay not available")

    def xwd_bytes_to_png(data):  # type: ignore[no-redef,misc]
        raise RuntimeError(_VDISPLAY_IMPORT_ERROR or "vdisplay not available")

    VirtualDisplaySession = None  # type: ignore[misc,assignment]

_MIRROR_WINDOW_TITLE = "testql-vdisplay-mirror"
_virtual_display_seq = 99


def _allocate_virtual_display() -> str:
    """Pick next Xvfb display number to avoid collisions between captures."""
    global _virtual_display_seq
    for _ in range(32):
        candidate = f":{_virtual_display_seq}"
        _virtual_display_seq += 1
        if _virtual_display_seq > 130:
            _virtual_display_seq = 99
        return candidate
    return ":99"


@dataclass
class CaptureResult:
    ok: bool
    path: str
    method: str = ""
    monitor: str | None = None
    window_count: int = 0
    width: int = 0
    height: int = 0
    scene_class: str | None = None
    virtual_display: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "path": self.path,
            "method": self.method,
            "monitor": self.monitor,
            "window_count": self.window_count,
            "width": self.width,
            "height": self.height,
            "scene_class": self.scene_class,
            "virtual_display": self.virtual_display,
            "error": self.error,
        }


def vdisplay_available() -> bool:
    return _VDISPLAY_AVAILABLE


def vdisplay_missing_message() -> str:
    if _VDISPLAY_AVAILABLE:
        return ""
    return (
        "vdisplay not installed — pip install -e ~/github/wronai/vdisplay[pillow] "
        f"({ _VDISPLAY_IMPORT_ERROR})"
    )


def resolve_display() -> str:
    if _VDISPLAY_AVAILABLE:
        return resolve_host_display(os.environ.get("DISPLAY"))
    return os.environ.get("DISPLAY", ":0").strip() or ":0"


def _format_window_id(window_id: str | int) -> str:
    raw = str(window_id).strip()
    if raw.lower().startswith("0x"):
        return raw
    return f"0x{int(raw):x}"


def _xwd_window_png(display: str, window_id: str | int) -> bytes | None:
    if not shutil_which("xwd"):
        return None
    hex_id = _format_window_id(window_id)
    proc = subprocess.run(
        ["xwd", "-id", hex_id, "-display", display],
        capture_output=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        return xwd_bytes_to_png(proc.stdout)
    except Exception:
        return None


def shutil_which(name: str) -> str | None:
    import shutil

    return shutil.which(name)


def is_blank_image(path: str | Path, *, locale: str = "pl") -> bool:
    """Heuristic blank/dark screen check via img2nl."""
    image = Path(path)
    if not image.is_file() or image.stat().st_size < 1024:
        return True
    try:
        from img2nl import analyze_image

        result = analyze_image(image, skip_thumbnail=True, locale=locale)
        if not result.ok:
            return True
        scene = (result.features or {}).get("scene", {})
        scene_class = str(scene.get("scene_class") or "")
        if scene_class in {"empty_dark_screen", "unchanged_screen", "flat_monochrome"}:
            dynamics = (result.features or {}).get("dynamics", {})
            spread = dynamics.get("dynamic_range") or dynamics.get("range") or 0
            if spread == 0 or scene_class == "empty_dark_screen":
                return True
        return False
    except ImportError:
        return False


def _scene_class(path: Path) -> str | None:
    try:
        from img2nl import analyze_image

        result = analyze_image(path, skip_thumbnail=True)
        if not result.ok:
            return None
        return (result.features or {}).get("scene", {}).get("scene_class")
    except ImportError:
        return None


def _primary_output(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    for item in outputs:
        if item.get("primary"):
            return item
    return outputs[0]


def _match_output_by_index(outputs: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
    for item in outputs:
        if item.get("monitor_index") == index or item.get("monitor_id") == index:
            return item
    if 0 <= index < len(outputs):
        return outputs[index]
    return None


def _match_output_by_name(outputs: list[dict[str, Any]], needle: str) -> dict[str, Any] | None:
    for item in outputs:
        name = str(item.get("name") or "").lower()
        if needle in name or name == needle:
            return item
    return None


def _resolve_monitor(
    monitor: str | int | None,
    outputs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not outputs:
        return None
    if monitor is None or str(monitor).lower() in {"primary", "default", "auto"}:
        return _primary_output(outputs)

    needle = str(monitor).strip().lower()
    if needle.isdigit():
        return _match_output_by_index(outputs, int(needle))
    return _match_output_by_name(outputs, needle)


def _windows_on_monitor(
    windows: list[dict[str, Any]],
    monitor: dict[str, Any],
) -> list[dict[str, Any]]:
    monitor_id = monitor.get("monitor_id")
    monitor_name = monitor.get("name")
    matched: list[dict[str, Any]] = []
    for window in windows:
        if monitor_id is not None and window.get("monitor_id") is not None:
            if int(window["monitor_id"]) == int(monitor_id):
                matched.append(window)
                continue
        if monitor_name and window.get("monitor_name") == monitor_name:
            matched.append(window)
    return matched


def _paste_window(
    canvas: Any,
    *,
    png_bytes: bytes,
    window: dict[str, Any],
    origin_x: int,
    origin_y: int,
) -> bool:
    from PIL import Image

    x = window.get("x")
    y = window.get("y")
    if x is None or y is None:
        return False
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    dx = int(x) - origin_x
    dy = int(y) - origin_y
    canvas.paste(image, (dx, dy))
    return True


@dataclass
class MonitorCanvas:
    image: Any
    monitor_name: str
    origin_x: int
    origin_y: int
    width: int
    height: int
    window_count: int


def build_monitor_canvas(
    *,
    monitor: str | int | None = None,
    display: str | None = None,
    background: tuple[int, int, int] = (30, 30, 30),
) -> MonitorCanvas | None:
    """Mirror host monitor content into an in-memory canvas (vdisplay window layout)."""
    if not _VDISPLAY_AVAILABLE:
        return None

    from PIL import Image

    disp = display or resolve_display()
    outputs = list(list_outputs(disp))
    target = _resolve_monitor(monitor, outputs)
    if target is None:
        return None

    px = int(target.get("x") or 0)
    py = int(target.get("y") or 0)
    pw = int(target.get("width") or 1920)
    ph = int(target.get("height") or 1080)
    monitor_name = str(target.get("name") or "primary")

    windows = list_capture_windows(display=disp)
    on_monitor = _windows_on_monitor(windows, target)

    canvas = Image.new("RGB", (pw, ph), background)
    placed = _composite_windows(
        canvas,
        display=disp,
        windows=on_monitor,
        origin_x=px,
        origin_y=py,
    )

    return MonitorCanvas(
        image=canvas,
        monitor_name=monitor_name,
        origin_x=px,
        origin_y=py,
        width=pw,
        height=ph,
        window_count=placed,
    )


def _viewer_script(image_path: str, width: int, height: int) -> str:
    return f"""
import tkinter as tk
from PIL import Image, ImageTk
root = tk.Tk()
root.title({_MIRROR_WINDOW_TITLE!r})
root.geometry("{width}x{height}+0+0")
root.overrideredirect(True)
im = Image.open({image_path!r})
photo = ImageTk.PhotoImage(im)
tk.Label(root, image=photo).pack()
root.mainloop()
"""


def _find_mirror_window(virtual_display: str) -> str | None:
    if not shutil_which("xdotool"):
        return None
    proc = subprocess.run(
        ["xdotool", "search", "--name", _MIRROR_WINDOW_TITLE],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        env={**os.environ, "DISPLAY": virtual_display},
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return proc.stdout.strip().splitlines()[0].strip()


def _capture_virtual_window(virtual_display: str, window_id: str) -> bytes | None:
    hex_id = _format_window_id(window_id)
    proc = subprocess.run(
        ["xwd", "-id", hex_id, "-display", virtual_display],
        capture_output=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        return None
    try:
        return xwd_bytes_to_png(proc.stdout)
    except Exception:
        return None


def _stop_mirror_resources(
    *,
    viewer: subprocess.Popen[Any] | None,
    session: Any | None,
    tmp_png: Path | None,
) -> None:
    if viewer is not None and viewer.poll() is None:
        viewer.terminate()
        try:
            viewer.wait(timeout=3)
        except subprocess.TimeoutExpired:
            viewer.kill()
    if session is not None:
        session.stop()
    if tmp_png is not None:
        tmp_png.unlink(missing_ok=True)


def _mirror_capture_result(
    *,
    out: Path,
    canvas: Any,
    vdisp: str,
    png_bytes: bytes | None,
    wid: str | None,
) -> CaptureResult:
    base = {
        "path": str(out),
        "monitor": canvas.monitor_name,
        "virtual_display": vdisp,
    }
    if not wid:
        return CaptureResult(ok=False, error="mirror viewer window not found on virtual display", **base)
    if not png_bytes:
        return CaptureResult(ok=False, error="xwd capture from virtual display failed", **base)

    out.write_bytes(png_bytes)
    meta = {
        "method": "vdisplay_mirror_virtual",
        "window_count": canvas.window_count,
        "width": canvas.width,
        "height": canvas.height,
    }
    if is_blank_image(out) and canvas.window_count > 0:
        return CaptureResult(
            ok=False,
            scene_class="empty_dark_screen",
            error="mirrored virtual capture is blank",
            **base,
            **meta,
        )
    return CaptureResult(ok=True, scene_class=_scene_class(out), **base, **meta)


def capture_monitor_mirror_virtual(
    path: str | Path,
    *,
    monitor: str | int | None = None,
    display: str | None = None,
    virtual_display: str | None = None,
) -> CaptureResult:
    """Mirror selected monitor into vdisplay Xvfb, capture via xwd (no Wayland portal)."""
    if not _VDISPLAY_AVAILABLE:
        return CaptureResult(ok=False, path=str(path), error=vdisplay_missing_message())

    if not shutil_which("Xvfb") or not shutil_which("xwd"):
        return CaptureResult(
            ok=False,
            path=str(path),
            error="mirror capture requires Xvfb and xwd (apt install xvfb x11-apps)",
        )

    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = build_monitor_canvas(monitor=monitor, display=display)
    if canvas is None:
        return CaptureResult(ok=False, path=str(out), error="monitor not found or vdisplay unavailable")

    vdisp_slot = virtual_display or _allocate_virtual_display()
    session = None
    viewer: subprocess.Popen[Any] | None = None
    tmp_png: Path | None = None

    try:
        session = VirtualDisplaySession.create(
            width=canvas.width,
            height=canvas.height,
            display=vdisp_slot,
        )
        session.start()
        vdisp = str(session.info().get("metadata", {}).get("display") or vdisp_slot)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_png = Path(tmp.name)
        canvas.image.save(tmp_png, format="PNG")

        viewer = subprocess.Popen(
            ["python3", "-c", _viewer_script(str(tmp_png), canvas.width, canvas.height)],
            env={**os.environ, "DISPLAY": vdisp},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.8)

        wid = _find_mirror_window(vdisp)
        png_bytes = _capture_virtual_window(vdisp, wid) if wid else None
        return _mirror_capture_result(out=out, canvas=canvas, vdisp=vdisp, png_bytes=png_bytes, wid=wid)
    except Exception as exc:
        return CaptureResult(ok=False, path=str(out), error=str(exc))
    finally:
        _stop_mirror_resources(viewer=viewer, session=session, tmp_png=tmp_png)


def capture_monitor_composite(
    path: str | Path,
    *,
    monitor: str | int | None = None,
    display: str | None = None,
    background: tuple[int, int, int] = (30, 30, 30),
) -> CaptureResult:
    """Direct composite save (fallback when virtual mirror unavailable)."""
    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas = build_monitor_canvas(monitor=monitor, display=display, background=background)
    if canvas is None:
        return CaptureResult(ok=False, path=str(out), error="monitor not found or vdisplay unavailable")

    canvas.image.save(out, format="PNG")
    if is_blank_image(out) and canvas.window_count > 0:
        return CaptureResult(
            ok=False,
            path=str(out),
            method="vdisplay_composite",
            monitor=canvas.monitor_name,
            window_count=canvas.window_count,
            width=canvas.width,
            height=canvas.height,
            scene_class="empty_dark_screen",
            error="composite capture is blank",
        )

    return CaptureResult(
        ok=True,
        path=str(out),
        method="vdisplay_composite",
        monitor=canvas.monitor_name,
        window_count=canvas.window_count,
        width=canvas.width,
        height=canvas.height,
        scene_class=_scene_class(out),
    )


def _desktop_bounds(outputs: list[dict[str, Any]]) -> tuple[int, int]:
    max_x = max(int(item.get("x") or 0) + int(item.get("width") or 0) for item in outputs)
    max_y = max(int(item.get("y") or 0) + int(item.get("height") or 0) for item in outputs)
    return max_x, max_y


def _composite_windows(
    canvas: Any,
    *,
    display: str,
    windows: list[dict[str, Any]],
    origin_x: int = 0,
    origin_y: int = 0,
) -> int:
    placed = 0
    for window in windows:
        wid = window.get("window_id")
        if not wid:
            continue
        png = _xwd_window_png(display, wid)
        if png and _paste_window(
            canvas,
            png_bytes=png,
            window=window,
            origin_x=origin_x,
            origin_y=origin_y,
        ):
            placed += 1
    return placed


def _finalize_desktop_composite(
    out: Path,
    *,
    placed: int,
    width: int,
    height: int,
) -> CaptureResult:
    base = {
        "path": str(out),
        "method": "vdisplay_desktop_composite",
        "window_count": placed,
        "width": width,
        "height": height,
    }
    if is_blank_image(out):
        return CaptureResult(ok=False, error="desktop composite is blank", **base)
    return CaptureResult(ok=True, **base)


def capture_desktop_composite(
    path: str | Path,
    *,
    display: str | None = None,
    background: tuple[int, int, int] = (30, 30, 30),
) -> CaptureResult:
    """Capture full virtual desktop by compositing all app windows."""
    if not _VDISPLAY_AVAILABLE:
        return CaptureResult(ok=False, path=str(path), error=vdisplay_missing_message())

    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    disp = display or resolve_display()
    outputs = list(list_outputs(disp))
    if not outputs:
        return CaptureResult(ok=False, path=str(out), error="no monitors from vdisplay")

    max_x, max_y = _desktop_bounds(outputs)
    from PIL import Image

    canvas = Image.new("RGB", (max_x, max_y), background)
    placed = _composite_windows(
        canvas,
        display=disp,
        windows=list_capture_windows(display=disp),
    )
    if placed == 0:
        return CaptureResult(ok=False, path=str(out), error="no windows captured")

    canvas.save(out, format="PNG")
    return _finalize_desktop_composite(out, placed=placed, width=max_x, height=max_y)


def _try_scrot_region_capture(
    out: Path,
    *,
    monitor: str | int | None,
    display: str | None,
) -> CaptureResult | None:
    if not _VDISPLAY_AVAILABLE:
        return None

    disp = display or resolve_display()
    outputs = list(list_outputs(disp))
    target = _resolve_monitor(monitor, outputs) or (outputs[0] if outputs else None)
    if target is None:
        return None

    x, y = int(target.get("x") or 0), int(target.get("y") or 0)
    width, height = int(target.get("width") or 0), int(target.get("height") or 0)
    try:
        data = capture_display_png(disp, region=(x, y, width, height))
        out.write_bytes(data)
    except Exception:
        return None

    if is_blank_image(out):
        return None
    return CaptureResult(
        ok=True,
        path=str(out),
        method="vdisplay_scrot_region",
        monitor=str(target.get("name")),
        width=width,
        height=height,
    )


def capture_via_vdisplay(
    path: str | Path,
    *,
    monitor: str | int | None = None,
    display: str | None = None,
    mirror_virtual: bool = True,
) -> CaptureResult:
    """Best-effort vdisplay capture: mirror→Xvfb → composite → scrot region."""
    out = Path(path).expanduser()
    attempts: list[CaptureResult] = []

    if mirror_virtual:
        mirror = capture_monitor_mirror_virtual(out, monitor=monitor, display=display)
        if mirror.ok:
            return mirror
        attempts.append(mirror)

    monitor_result = capture_monitor_composite(out, monitor=monitor, display=display)
    if monitor_result.ok:
        return monitor_result
    attempts.append(monitor_result)

    desktop_result = capture_desktop_composite(out, display=display)
    if desktop_result.ok:
        return desktop_result
    attempts.append(desktop_result)

    region_result = _try_scrot_region_capture(out, monitor=monitor, display=display)
    if region_result is not None:
        return region_result

    last_error = attempts[-1].error if attempts else "vdisplay capture failed"
    return CaptureResult(ok=False, path=str(out), error=last_error or "vdisplay capture failed")


def read_capture_meta(path: str | Path) -> dict[str, Any] | None:
    meta_path = Path(str(path) + ".vdisplay.json")
    if not meta_path.is_file():
        return None
    import json

    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_capture_with_meta(path: str | Path, result: CaptureResult) -> None:
    meta_path = Path(str(path) + ".vdisplay.json")
    import json

    meta_path.write_text(json.dumps(result.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
