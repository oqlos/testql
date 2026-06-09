"""Native desktop application control mixin for OqlInterpreter."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus
from testql.desktop import get_desktop_backend
from testql.desktop.element_assert import evaluate_element_assert
from testql.desktop.models import DesktopSession
from testql.desktop import vision as desktop_vision

from ._parser import OqlLine


class DesktopMixin:
    """Mixin for native OS desktop control (windows, focus, click, type, keys).

    Commands:
      - DESKTOP_LIST — list open windows (wmctrl)
      - DESKTOP_FOCUS "title" | window_id — raise/focus window
      - DESKTOP_LAUNCH "/path/to/app" [args] — start native application
      - DESKTOP_CLICK x y — click screen coordinates
      - DESKTOP_TYPE "text" — type into focused window
      - DESKTOP_KEY Return | ctrl+s — send key combo
      - DESKTOP_CAPTURE "file.png" — full-screen screenshot
      - DESKTOP_ASSERT_WINDOW "title" — assert window exists
      - DESKTOP_MONITORS — list connected monitors (vdisplay / xrandr)
      - DESKTOP_INSPECT ["file.png"] — discover monitors, windows, vision summary
      - DESKTOP_DESCRIBE "file.png" — img2nl heuristic scene description
      - DESKTOP_ANALYZE "file.png" [out.json] — imgl OCR/layout analysis
      - DESKTOP_ASSERT_TEXT "needle" ["file.png"] — assert visible text (imgl OCR)
      - DESKTOP_ASSERT_ELEMENTS min ["file.png"] — assert imgl layout element count
      - DESKTOP_CLICK_TEXT "label" ["file.png"] — click element by OCR label/text
      - DESKTOP_STOP — terminate launched apps from this session
    """

    _desktop_session: DesktopSession | None = None
    _desktop_backend: Any = None

    def _desktop(self):
        if self._desktop_backend is None:
            self._desktop_session = self._desktop_session or DesktopSession()
            self._desktop_backend = get_desktop_backend(self._desktop_session)
        return self._desktop_backend

    def _cmd_desktop_list(self, args: str, line: OqlLine) -> None:
        if self.dry_run:
            self.out.step("🪟", "DESKTOP_LIST (dry-run)")
            self.results.append(StepResult(name="DESKTOP_LIST", status=StepStatus.PASSED))
            return

        windows = self._desktop().list_windows()
        self.out.step("🪟", f"DESKTOP_LIST: {len(windows)} window(s)")
        for window in windows[:20]:
            active = " *" if window.active else ""
            self.out.step("  ", f"{window.id} {window.title[:60]}{active}")
        self.vars.set("desktop_window_count", str(len(windows)))
        self.results.append(
            StepResult(
                name="DESKTOP_LIST",
                status=StepStatus.PASSED,
                message=f"{len(windows)} windows",
            ),
        )

    def _cmd_desktop_focus(self, args: str, line: OqlLine) -> None:
        target = args.strip().strip('"\'')
        if not target:
            self.out.fail(f"L{line.number}: DESKTOP_FOCUS requires title or window id")
            return

        if self.dry_run:
            self.out.step("🎯", f'DESKTOP_FOCUS "{target}" (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_FOCUS "{target}"', status=StepStatus.PASSED),
            )
            return

        window_id = target if target.lower().startswith("0x") else None
        title = None if window_id else target
        focused = self._desktop().focus_window(title=title, window_id=window_id)
        if focused is None:
            self.out.fail(f'DESKTOP_FOCUS: no window matching "{target}"')
            self.results.append(
                StepResult(
                    name=f'DESKTOP_FOCUS "{target}"',
                    status=StepStatus.FAILED,
                    message="window not found",
                ),
            )
            return

        self.out.step("🎯", f'DESKTOP_FOCUS → {focused.id} "{focused.title[:50]}"')
        self.vars.set("desktop_focused_window", focused.id)
        self.vars.set("desktop_focused_title", focused.title)
        self.results.append(
            StepResult(name=f'DESKTOP_FOCUS "{target}"', status=StepStatus.PASSED),
        )

    def _cmd_desktop_launch(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        if not parts:
            self.out.fail(f"L{line.number}: DESKTOP_LAUNCH requires executable path")
            return

        executable = parts[0]
        extra = " ".join(parts[1:])

        if self.dry_run:
            self.out.step("🚀", f'DESKTOP_LAUNCH "{executable}" (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_LAUNCH "{executable}"', status=StepStatus.PASSED),
            )
            return

        try:
            pid = self._desktop().launch(executable, extra)
        except (OSError, FileNotFoundError, RuntimeError) as exc:
            self.out.fail(f"DESKTOP_LAUNCH error: {exc}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_LAUNCH "{executable}"',
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        self.out.step("🚀", f'DESKTOP_LAUNCH "{executable}" pid={pid}')
        self.vars.set("desktop_last_pid", str(pid))
        self.results.append(
            StepResult(name=f'DESKTOP_LAUNCH "{executable}"', status=StepStatus.PASSED),
        )

    def _cmd_desktop_click(self, args: str, line: OqlLine) -> None:
        parts = args.strip().split()
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: DESKTOP_CLICK requires x y")
            return
        try:
            x, y = int(parts[0]), int(parts[1])
        except ValueError:
            self.out.fail(f"L{line.number}: DESKTOP_CLICK x y must be integers")
            return

        if self.dry_run:
            self.out.step("🖱️", f"DESKTOP_CLICK {x} {y} (dry-run)")
            self.results.append(
                StepResult(name=f"DESKTOP_CLICK {x} {y}", status=StepStatus.PASSED),
            )
            return

        try:
            self._desktop().click(x, y)
        except RuntimeError as exc:
            self.out.fail(f"DESKTOP_CLICK error: {exc}")
            self.results.append(
                StepResult(
                    name=f"DESKTOP_CLICK {x} {y}",
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        self.out.step("🖱️", f"DESKTOP_CLICK {x} {y}")
        self.results.append(
            StepResult(name=f"DESKTOP_CLICK {x} {y}", status=StepStatus.PASSED),
        )

    def _cmd_desktop_type(self, args: str, line: OqlLine) -> None:
        text = args.strip().strip('"\'')
        if not text:
            self.out.fail(f"L{line.number}: DESKTOP_TYPE requires text")
            return

        if self.dry_run:
            self.out.step("⌨️", f'DESKTOP_TYPE "{text[:30]}" (dry-run)')
            self.results.append(
                StepResult(name="DESKTOP_TYPE", status=StepStatus.PASSED),
            )
            return

        try:
            self._desktop().type_text(text)
        except RuntimeError as exc:
            self.out.fail(f"DESKTOP_TYPE error: {exc}")
            self.results.append(
                StepResult(name="DESKTOP_TYPE", status=StepStatus.ERROR, message=str(exc)),
            )
            return

        self.out.step("⌨️", f'DESKTOP_TYPE "{text[:30]}"')
        self.results.append(StepResult(name="DESKTOP_TYPE", status=StepStatus.PASSED))

    def _cmd_desktop_key(self, args: str, line: OqlLine) -> None:
        combo = args.strip().strip('"\'')
        if not combo:
            self.out.fail(f"L{line.number}: DESKTOP_KEY requires key combo")
            return

        if self.dry_run:
            self.out.step("⌨️", f"DESKTOP_KEY {combo} (dry-run)")
            self.results.append(
                StepResult(name=f"DESKTOP_KEY {combo}", status=StepStatus.PASSED),
            )
            return

        try:
            self._desktop().send_key(combo)
        except RuntimeError as exc:
            self.out.fail(f"DESKTOP_KEY error: {exc}")
            self.results.append(
                StepResult(
                    name=f"DESKTOP_KEY {combo}",
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        self.out.step("⌨️", f"DESKTOP_KEY {combo}")
        self.results.append(
            StepResult(name=f"DESKTOP_KEY {combo}", status=StepStatus.PASSED),
        )

    def _cmd_desktop_capture(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        filename = parts[0].strip('"\'') if parts else "desktop.png"
        monitor = parts[1] if len(parts) > 1 else None

        if self.dry_run:
            label = f' "{monitor}"' if monitor else ""
            self.out.step("📸", f'DESKTOP_CAPTURE "{filename}"{label} (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_CAPTURE "{filename}"', status=StepStatus.PASSED),
            )
            return

        try:
            self._desktop().screenshot(filename, monitor=monitor)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            self.out.fail(f"DESKTOP_CAPTURE error: {exc}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_CAPTURE "{filename}"',
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        meta_note = ""
        meta_path = Path(f"{filename}.vdisplay.json")
        if meta_path.is_file():
            try:
                import json

                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                method = meta.get("method") or "direct"
                windows = meta.get("window_count")
                vdisp = meta.get("virtual_display")
                meta_note = f" [{method}"
                if vdisp:
                    meta_note += f" @ {vdisp}"
                if windows:
                    meta_note += f", {windows} windows"
                meta_note += "]"
            except Exception:
                pass

        self.out.step("📸", f'DESKTOP_CAPTURE → "{filename}"{meta_note}')
        self.vars.set("desktop_last_capture", filename)
        self.results.append(
            StepResult(name=f'DESKTOP_CAPTURE "{filename}"', status=StepStatus.PASSED),
        )

    def _cmd_desktop_assert_window(self, args: str, line: OqlLine) -> None:
        title = args.strip().strip('"\'')
        if not title:
            self.out.fail(f"L{line.number}: DESKTOP_ASSERT_WINDOW requires title")
            return

        if self.dry_run:
            self.out.step("✅", f'DESKTOP_ASSERT_WINDOW "{title}" (dry-run)')
            self.results.append(
                StepResult(
                    name=f'DESKTOP_ASSERT_WINDOW "{title}"',
                    status=StepStatus.PASSED,
                ),
            )
            return

        windows = self._desktop().list_windows()
        needle = title.lower()
        match = next((w for w in windows if needle in w.title.lower()), None)
        if match is None:
            self.out.step("❌", f'DESKTOP_ASSERT_WINDOW "{title}" not found')
            self.results.append(
                StepResult(
                    name=f'DESKTOP_ASSERT_WINDOW "{title}"',
                    status=StepStatus.FAILED,
                    message="window not found",
                ),
            )
            return

        self.out.step("✅", f'DESKTOP_ASSERT_WINDOW "{match.title[:50]}"')
        self.results.append(
            StepResult(
                name=f'DESKTOP_ASSERT_WINDOW "{title}"',
                status=StepStatus.PASSED,
            ),
        )

    def _parse_image_args(self, args: str) -> tuple[str | None, str | None]:
        """Parse optional image path and quoted needle from DESKTOP_* args."""
        parts = shlex.split(args.strip()) if args.strip() else []
        image: str | None = None
        needle: str | None = None
        for part in parts:
            if part.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image = part
            elif needle is None:
                needle = part.strip('"\'')
        return needle, image

    def _resolve_capture_path(self, image: str | None, *, default: str) -> str:
        if image:
            return image
        cached = self.vars.get("desktop_last_capture")
        if cached:
            return str(cached)
        return default

    def _ensure_capture(self, image: str | None, *, default: str, monitor: str | int | None = "primary") -> str:
        path = self._resolve_capture_path(image, default=default)
        if Path(path).is_file() and not self._capture_is_stale_blank(path):
            return path
        if self.dry_run:
            return path
        self._desktop().screenshot(path, monitor=monitor)
        self.vars.set("desktop_last_capture", path)
        return path

    def _capture_is_stale_blank(self, path: str | Path) -> bool:
        try:
            from testql.desktop.vdisplay_capture import is_blank_image

            return is_blank_image(path)
        except ImportError:
            return False

    def _cmd_desktop_monitors(self, args: str, line: OqlLine) -> None:
        if self.dry_run:
            self.out.step("🖥️", "DESKTOP_MONITORS (dry-run)")
            self.results.append(StepResult(name="DESKTOP_MONITORS", status=StepStatus.PASSED))
            return

        monitors = desktop_vision.list_monitors()
        self.out.step("🖥️", f"DESKTOP_MONITORS: {len(monitors)} monitor(s)")
        for monitor in monitors:
            label = monitor.get("name") or monitor.get("label") or "?"
            geom = monitor.get("geometry") or f"{monitor.get('width')}x{monitor.get('height')}"
            primary = " primary" if monitor.get("primary") else ""
            self.out.step("  ", f"{label} {geom}{primary}")
        self.vars.set("desktop_monitor_count", str(len(monitors)))
        self.results.append(
            StepResult(
                name="DESKTOP_MONITORS",
                status=StepStatus.PASSED,
                message=f"{len(monitors)} monitors",
            ),
        )

    def _cmd_desktop_inspect(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        capture = parts[0] if parts else "examples/desktop/inspect.png"

        if self.dry_run:
            self.out.step("🔍", f'DESKTOP_INSPECT "{capture}" (dry-run)')
            self.results.append(StepResult(name="DESKTOP_INSPECT", status=StepStatus.PASSED))
            return

        payload = desktop_vision.inspect_environment(capture_path=capture)
        self.out.step("🔍", "DESKTOP_INSPECT")
        self.out.step("  ", f"display={payload.display_server} {payload.display}")
        self.out.step("  ", f"monitors={len(payload.monitors)} windows={len(payload.windows)}")
        for window in payload.windows[:12]:
            title = str(window.get("title") or window.get("app_label") or "?")
            self.out.step("  ", f"window: {title[:70]}")
        if payload.describe and payload.describe.get("ok"):
            self.out.step("  ", f"img2nl: {payload.describe.get('scene_class')} — {str(payload.describe.get('text', ''))[:80]}")
        if payload.layout and payload.layout.get("ok"):
            self.out.step(
                "  ",
                f"imgl: {payload.layout.get('window_count')} windows, "
                f"{payload.layout.get('element_count')} elements",
            )
        self.vars.set("desktop_last_capture", capture)
        self.vars.set("desktop_inspect_json", json.dumps(payload.as_dict(), ensure_ascii=False))
        self.results.append(
            StepResult(
                name="DESKTOP_INSPECT",
                status=StepStatus.PASSED,
                message=f"monitors={len(payload.monitors)} windows={len(payload.windows)}",
            ),
        )

    def _cmd_desktop_describe(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        if not parts:
            self.out.fail(f"L{line.number}: DESKTOP_DESCRIBE requires image path")
            return
        image = parts[0]

        if self.dry_run:
            self.out.step("📝", f'DESKTOP_DESCRIBE "{image}" (dry-run)')
            self.results.append(StepResult(name="DESKTOP_DESCRIBE", status=StepStatus.PASSED))
            return

        result = desktop_vision.describe_image(image)
        if not result.get("ok"):
            self.out.fail(f"DESKTOP_DESCRIBE error: {result.get('error', 'unknown')}")
            self.results.append(
                StepResult(
                    name="DESKTOP_DESCRIBE",
                    status=StepStatus.ERROR,
                    message=str(result.get("error")),
                ),
            )
            return

        summary = str(result.get("text") or "")[:120]
        scene = result.get("scene_class") or "unknown"
        self.out.step("📝", f"DESKTOP_DESCRIBE {scene}: {summary}")
        self.vars.set("desktop_scene_class", str(scene))
        self.vars.set("desktop_describe_text", str(result.get("text") or ""))
        self.results.append(
            StepResult(name="DESKTOP_DESCRIBE", status=StepStatus.PASSED, message=scene),
        )

    def _cmd_desktop_analyze(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        if not parts:
            self.out.fail(f"L{line.number}: DESKTOP_ANALYZE requires image path")
            return
        image = parts[0]
        out_json = parts[1] if len(parts) > 1 else None

        if self.dry_run:
            self.out.step("🧩", f'DESKTOP_ANALYZE "{image}" (dry-run)')
            self.results.append(StepResult(name="DESKTOP_ANALYZE", status=StepStatus.PASSED))
            return

        result = desktop_vision.analyze_layout(image)
        if not result.get("ok"):
            self.out.fail(f"DESKTOP_ANALYZE error: {result.get('error', 'unknown')}")
            self.results.append(
                StepResult(
                    name="DESKTOP_ANALYZE",
                    status=StepStatus.ERROR,
                    message=str(result.get("error")),
                ),
            )
            return

        if out_json:
            Path(out_json).parent.mkdir(parents=True, exist_ok=True)
            Path(out_json).write_text(
                json.dumps(result.get("scene_json", {}), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        self.out.step(
            "🧩",
            f"DESKTOP_ANALYZE: {result.get('window_count')} windows, "
            f"{result.get('element_count')} elements",
        )
        samples = result.get("text_samples") or []
        for sample in samples[:8]:
            self.out.step("  ", str(sample)[:70])
        self.vars.set("desktop_element_count", str(result.get("element_count") or 0))
        self.vars.set("desktop_window_count", str(result.get("window_count") or 0))
        self.results.append(
            StepResult(
                name="DESKTOP_ANALYZE",
                status=StepStatus.PASSED,
                message=f"elements={result.get('element_count')}",
            ),
        )

    def _cmd_desktop_assert_text(self, args: str, line: OqlLine) -> None:
        needle, image = self._parse_image_args(args)
        if not needle:
            self.out.fail(f"L{line.number}: DESKTOP_ASSERT_TEXT requires text needle")
            return

        if self.dry_run:
            self.out.step("✅", f'DESKTOP_ASSERT_TEXT "{needle}" (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_ASSERT_TEXT "{needle}"', status=StepStatus.PASSED),
            )
            return

        capture = self._ensure_capture(image, default="examples/desktop/assert-text.png")
        result = desktop_vision.find_text(capture, needle)
        if not result.get("ok"):
            self.out.fail(f"DESKTOP_ASSERT_TEXT error: {result.get('error', 'unknown')}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_ASSERT_TEXT "{needle}"',
                    status=StepStatus.ERROR,
                    message=str(result.get("error")),
                ),
            )
            return

        if not result.get("found"):
            self.out.step("❌", f'DESKTOP_ASSERT_TEXT "{needle}" not found')
            self.results.append(
                StepResult(
                    name=f'DESKTOP_ASSERT_TEXT "{needle}"',
                    status=StepStatus.FAILED,
                    message="text not found",
                ),
            )
            return

        self.out.step("✅", f'DESKTOP_ASSERT_TEXT "{needle}"')
        self.results.append(
            StepResult(name=f'DESKTOP_ASSERT_TEXT "{needle}"', status=StepStatus.PASSED),
        )

    def _cmd_desktop_assert_elements(self, args: str, line: OqlLine) -> None:
        parts = shlex.split(args.strip()) if args.strip() else []
        if not parts:
            self.out.fail(f"L{line.number}: DESKTOP_ASSERT_ELEMENTS requires minimum count")
            return
        try:
            minimum = int(parts[0])
        except ValueError:
            self.out.fail(f"L{line.number}: DESKTOP_ASSERT_ELEMENTS count must be integer")
            return

        image: str | None = None
        for part in parts[1:]:
            if part.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image = part.strip('"\'')
                break

        if self.dry_run:
            self.out.step("✅", f"DESKTOP_ASSERT_ELEMENTS >= {minimum} (dry-run)")
            self.results.append(
                StepResult(name=f"DESKTOP_ASSERT_ELEMENTS >= {minimum}", status=StepStatus.PASSED),
            )
            return

        capture = self._ensure_capture(image, default="examples/desktop/assert-elements.png")
        from testql.desktop.vdisplay_capture import read_capture_meta

        meta = read_capture_meta(capture) or {}
        mirrored_windows = int(meta.get("window_count") or 0)

        result = desktop_vision.analyze_layout(capture)
        if not result.get("ok"):
            self.out.fail(f"DESKTOP_ASSERT_ELEMENTS error: {result.get('error', 'unknown')}")
            self.results.append(
                StepResult(
                    name=f"DESKTOP_ASSERT_ELEMENTS >= {minimum}",
                    status=StepStatus.ERROR,
                    message=str(result.get("error")),
                ),
            )
            return

        count = int(result.get("element_count") or 0)
        outcome = evaluate_element_assert(
            minimum=minimum,
            element_count=count,
            mirrored_windows=mirrored_windows,
        )
        icon = "✅" if outcome.passed else "❌"
        self.out.step(icon, outcome.step_text)
        self.vars.set("desktop_element_count", str(count))
        if mirrored_windows:
            self.vars.set("desktop_mirrored_window_count", str(mirrored_windows))
        self.results.append(
            StepResult(
                name=f"DESKTOP_ASSERT_ELEMENTS >= {minimum}",
                status=StepStatus.PASSED if outcome.passed else StepStatus.FAILED,
                message=outcome.message,
            ),
        )

    def _cmd_desktop_click_text(self, args: str, line: OqlLine) -> None:
        needle, image = self._parse_image_args(args)
        if not needle:
            self.out.fail(f"L{line.number}: DESKTOP_CLICK_TEXT requires label/text")
            return

        if self.dry_run:
            self.out.step("🖱️", f'DESKTOP_CLICK_TEXT "{needle}" (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_CLICK_TEXT "{needle}"', status=StepStatus.PASSED),
            )
            return

        capture = self._ensure_capture(image, default="examples/desktop/click-text.png")
        result = desktop_vision.find_text(capture, needle)
        if not result.get("ok"):
            self.out.fail(f"DESKTOP_CLICK_TEXT error: {result.get('error', 'unknown')}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_CLICK_TEXT "{needle}"',
                    status=StepStatus.ERROR,
                    message=str(result.get("error")),
                ),
            )
            return

        coords = result.get("coords")
        if not coords:
            self.out.fail(f'DESKTOP_CLICK_TEXT: "{needle}" found in OCR but no clickable element')
            self.results.append(
                StepResult(
                    name=f'DESKTOP_CLICK_TEXT "{needle}"',
                    status=StepStatus.FAILED,
                    message="no clickable coords",
                ),
            )
            return

        x, y = int(coords["x"]), int(coords["y"])
        try:
            self._desktop().click(x, y)
        except RuntimeError as exc:
            self.out.fail(f"DESKTOP_CLICK_TEXT error: {exc}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_CLICK_TEXT "{needle}"',
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        self.out.step("🖱️", f'DESKTOP_CLICK_TEXT "{needle}" @ {x},{y}')
        self.results.append(
            StepResult(name=f'DESKTOP_CLICK_TEXT "{needle}"', status=StepStatus.PASSED),
        )

    def _cmd_desktop_stop(self, args: str, line: OqlLine) -> None:
        if self.dry_run:
            self.out.step("🛑", "DESKTOP_STOP (dry-run)")
            self.results.append(StepResult(name="DESKTOP_STOP", status=StepStatus.PASSED))
            return

        import signal

        backend = self._desktop()
        stopped = 0
        for pid in list(backend.session.launched_pids):
            try:
                os.kill(pid, signal.SIGTERM)
                stopped += 1
            except OSError:
                pass
        backend.session.launched_pids.clear()
        self.out.step("🛑", f"DESKTOP_STOP: sent SIGTERM to {stopped} process(es)")
        self.results.append(
            StepResult(
                name="DESKTOP_STOP",
                status=StepStatus.PASSED,
                message=f"stopped={stopped}",
            ),
        )
