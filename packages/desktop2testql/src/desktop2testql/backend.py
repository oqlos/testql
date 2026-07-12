"""Linux desktop control backend (wmctrl / xdotool / ydotool / wtype)."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from desktop2testql.models import DesktopSession, DesktopWindow
from desktop2testql.screenshot_tools import screenshot_candidates, try_screenshot_candidates
from desktop2testql.wmctrl import parse_wmctrl_listing


def _parse_xdotool_geometry(shell_output: str) -> tuple[int, int, int, int]:
    x = y = width = height = 0
    for line in shell_output.splitlines():
        key, _, value = line.partition("=")
        if key == "X":
            x = int(value or 0)
        elif key == "Y":
            y = int(value or 0)
        elif key == "WIDTH":
            width = int(value or 0)
        elif key == "HEIGHT":
            height = int(value or 0)
    return x, y, width, height


def _desktop_window_from_vdisplay(item: dict) -> DesktopWindow | None:
    from desktop2testql.window_discovery import window_display_title, window_to_hex_id

    wid = item.get("window_id")
    if wid is None:
        return None
    return DesktopWindow(
        id=window_to_hex_id(wid),
        title=window_display_title(item),
        x=int(item.get("x") or 0),
        y=int(item.get("y") or 0),
        width=int(item.get("width") or 0),
        height=int(item.get("height") or 0),
    )


def _match_window_by_vdisplay_title(
    title: str,
    windows: list[DesktopWindow],
) -> DesktopWindow | None:
    try:
        from desktop2testql.window_discovery import list_capture_windows, window_matches
    except ImportError:
        return None

    for item in list_capture_windows():
        if not window_matches(item, title):
            continue
        candidate = _desktop_window_from_vdisplay(item)
        if candidate is None:
            continue
        for window in windows:
            if window.id.lower() == candidate.id.lower():
                return window
        return candidate
    return None


def _run(
    argv: list[str],
    *,
    timeout: float = 10.0,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = None
    if env is not None:
        run_env = {**os.environ, **env}
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=run_env,
    )


def detect_display_server() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


class DesktopBackend(ABC):
    @property
    @abstractmethod
    def display_server(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def tools(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_windows(self) -> list[DesktopWindow]:
        raise NotImplementedError

    @abstractmethod
    def focus_window(
        self,
        *,
        title: str | None = None,
        window_id: str | None = None,
    ) -> DesktopWindow | None:
        raise NotImplementedError

    @abstractmethod
    def launch(self, executable: str, extra_args: str = "") -> int:
        """Launch app; return PID."""
        raise NotImplementedError

    @abstractmethod
    def click(self, x: int, y: int, *, button: int = 1) -> None:
        raise NotImplementedError

    @abstractmethod
    def type_text(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_key(self, combo: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def screenshot(self, path: str) -> None:
        raise NotImplementedError


class LinuxDesktopBackend(DesktopBackend):
    """Best-effort Linux desktop automation using installed host tools."""

    def __init__(self, session: DesktopSession | None = None) -> None:
        self._session = session or DesktopSession()
        self._display_server = detect_display_server()

    @property
    def session(self) -> DesktopSession:
        return self._session

    @property
    def display_server(self) -> str:
        return self._display_server

    @property
    def tools(self) -> list[str]:
        found: list[str] = []
        for name in ("wmctrl", "xdotool", "wtype", "ydotool", "grim", "scrot", "import"):
            if shutil.which(name):
                found.append(name)
        return found

    def list_windows(self) -> list[DesktopWindow]:
        windows = self._list_windows_vdisplay()
        if not windows and shutil.which("wmctrl"):
            proc = _run(["wmctrl", "-l", "-G"])
            if proc.returncode == 0 and proc.stdout.strip():
                windows = parse_wmctrl_listing(proc.stdout)
        if not windows and shutil.which("xdotool"):
            windows = self._list_windows_xdotool()

        active_id = self._active_window_id()
        if active_id:
            for window in windows:
                if window.id.lower() == active_id.lower():
                    window.active = True
        return windows

    def _list_windows_vdisplay(self) -> list[DesktopWindow]:
        try:
            from desktop2testql.window_discovery import list_capture_windows
        except ImportError:
            return []

        windows: list[DesktopWindow] = []
        for item in list_capture_windows():
            window = _desktop_window_from_vdisplay(item)
            if window is not None:
                windows.append(window)
        return windows

    def _list_windows_xdotool(self) -> list[DesktopWindow]:
        proc = _run(["xdotool", "search", "--onlyvisible", "--name", ""])
        if proc.returncode != 0 or not proc.stdout.strip():
            return []

        windows: list[DesktopWindow] = []
        for raw_id in proc.stdout.split():
            wid = raw_id.strip()
            if not wid.isdigit():
                continue
            hex_id = f"0x{int(wid):x}"
            title_proc = _run(["xdotool", "getwindowname", wid])
            title = title_proc.stdout.strip() if title_proc.returncode == 0 else ""
            x = y = width = height = 0
            geom_proc = _run(["xdotool", "getwindowgeometry", "--shell", wid])
            if geom_proc.returncode == 0:
                x, y, width, height = _parse_xdotool_geometry(geom_proc.stdout)
            if title or width > 0:
                windows.append(
                    DesktopWindow(
                        id=hex_id,
                        title=title or f"window-{wid}",
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                    ),
                )
        return windows

    def _active_window_id(self) -> str | None:
        if not shutil.which("xdotool"):
            return None
        proc = _run(["xdotool", "getactivewindow"])
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        window_id = proc.stdout.strip()
        if window_id.isdigit():
            return f"0x{int(window_id):x}"
        return window_id

    def _match_window(
        self,
        windows: list[DesktopWindow],
        *,
        title: str | None,
        window_id: str | None,
    ) -> DesktopWindow | None:
        if window_id:
            for window in windows:
                if window.id.lower() == window_id.lower():
                    return window
        if title:
            matched = _match_window_by_vdisplay_title(title, windows)
            if matched is not None:
                return matched

            needle = title.lower()
            for window in windows:
                if needle in window.title.lower():
                    return window
        return None

    def focus_window(
        self,
        *,
        title: str | None = None,
        window_id: str | None = None,
    ) -> DesktopWindow | None:
        windows = self.list_windows()
        target = self._match_window(windows, title=title, window_id=window_id)
        if target is None:
            return None

        focused = False
        if shutil.which("wmctrl"):
            if window_id or target.id:
                wid = window_id or target.id
                proc = _run(["wmctrl", "-ia", wid])
                focused = proc.returncode == 0
            elif title:
                proc = _run(["wmctrl", "-a", title])
                focused = proc.returncode == 0

        if not focused and shutil.which("xdotool") and target.id:
            wid = target.id
            if wid.lower().startswith("0x"):
                wid = str(int(wid, 16))
            proc = _run(["xdotool", "windowactivate", wid])
            focused = proc.returncode == 0

        if focused:
            self._session.focused_window_id = target.id
            self._session.focused_title = target.title
            target.active = True
            return target
        return None

    def launch(self, executable: str, extra_args: str = "") -> int:
        path = Path(executable).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"executable not found: {executable}")

        argv = [str(path)]
        if extra_args.strip():
            argv.extend(shlex.split(extra_args))
        proc = subprocess.Popen(argv)  # noqa: S603
        self._session.launched_pids.append(proc.pid)
        return proc.pid

    def click(self, x: int, y: int, *, button: int = 1) -> None:
        if self.display_server == "wayland":
            self._click_wayland(x, y, button=button)
            return
        self._click_x11(x, y, button=button)

    def _click_x11(self, x: int, y: int, *, button: int) -> None:
        if not shutil.which("xdotool"):
            raise RuntimeError("xdotool not installed (required for X11 click)")
        proc = _run(["xdotool", "mousemove", str(x), str(y), "click", str(button)])
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "xdotool click failed")

    def _click_wayland(self, x: int, y: int, *, button: int) -> None:
        if shutil.which("ydotool"):
            # ydotool: mousemove abs x y, then click
            move = _run(["ydotool", "mousemove", "--absolute", str(x), str(y)])
            if move.returncode != 0:
                raise RuntimeError(move.stderr.strip() or "ydotool mousemove failed")
            click = _run(["ydotool", "click", str(button)])
            if click.returncode != 0:
                raise RuntimeError(click.stderr.strip() or "ydotool click failed")
            return
        raise RuntimeError(
            "Wayland click requires ydotool (install: apt install ydotool; "
            "start ydotoold if needed)",
        )

    def type_text(self, text: str) -> None:
        if self.display_server == "wayland":
            if not shutil.which("wtype"):
                raise RuntimeError("Wayland typing requires wtype")
            proc = _run(["wtype", text])
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "wtype failed")
            return

        if not shutil.which("xdotool"):
            raise RuntimeError("xdotool not installed (required for X11 typing)")
        proc = _run(["xdotool", "type", "--delay", "12", "--", text])
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "xdotool type failed")

    def send_key(self, combo: str) -> None:
        normalized = combo.strip().lower().replace("+", " ")
        parts = normalized.split()

        if self.display_server == "wayland":
            if not shutil.which("wtype"):
                raise RuntimeError("Wayland key events require wtype")
            if len(parts) == 1:
                proc = _run(["wtype", "-k", parts[0]])
            else:
                # wtype -M ctrl -k s -m ctrl
                argv = ["wtype"]
                for mod in parts[:-1]:
                    argv.extend(["-M", mod])
                argv.extend(["-k", parts[-1]])
                for mod in reversed(parts[:-1]):
                    argv.extend(["-m", mod])
                proc = _run(argv)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "wtype key failed")
            return

        if not shutil.which("xdotool"):
            raise RuntimeError("xdotool not installed (required for X11 keys)")
        proc = _run(["xdotool", "key", combo])
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "xdotool key failed")

    def screenshot(self, path: str, *, monitor: str | int | None = None) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if self.display_server == "wayland" and self._screenshot_vdisplay(out, monitor=monitor):
            return

        candidates = screenshot_candidates(display_server=self.display_server, output=out)
        errors = try_screenshot_candidates(
            candidates,
            output=out,
            run_fn=_run,
            is_blank=self._screenshot_is_blank,
        )
        if out.is_file() and not self._screenshot_is_blank(out):
            return

        if self._screenshot_mss(out) and not self._screenshot_is_blank(out):
            return
        if out.is_file():
            errors.append("mss: blank capture")

        if self._screenshot_vdisplay(out, monitor=monitor):
            return

        hint = "; ".join(errors) if errors else "no screenshot tool found"
        raise RuntimeError(
            f"desktop screenshot failed ({hint}). "
            "On GNOME Wayland use vdisplay mirror: pip install -e ~/github/wronai/vdisplay[pillow]",
        )

    def _screenshot_is_blank(self, out: Path) -> bool:
        try:
            from desktop2testql.vdisplay_capture import is_blank_image

            return is_blank_image(out)
        except ImportError:
            return False

    def _screenshot_vdisplay(self, out: Path, *, monitor: str | int | None = None) -> bool:
        try:
            from desktop2testql.vdisplay_capture import capture_via_vdisplay, save_capture_with_meta

            result = capture_via_vdisplay(out, monitor=monitor)
            if result.ok:
                save_capture_with_meta(out, result)
                return True
        except ImportError:
            return False
        except Exception:
            return False
        return False

    def _screenshot_mss(self, out: Path) -> bool:
        try:
            import mss
            import mss.tools
        except ImportError:
            return False
        try:
            with mss.mss() as grabber:
                shot = grabber.grab(grabber.monitors[0])
                mss.tools.to_png(shot.rgb, shot.size, output=str(out))
            return out.is_file() and out.stat().st_size > 0
        except Exception:
            return False


def get_desktop_backend(session: DesktopSession | None = None) -> DesktopBackend:
    """Return platform desktop backend (Linux today)."""
    return LinuxDesktopBackend(session=session)
