"""Native desktop application control mixin for OqlInterpreter."""

from __future__ import annotations

import os
import shlex
from typing import Any

from testql.base import StepResult, StepStatus
from testql.desktop import get_desktop_backend
from testql.desktop.models import DesktopSession

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
        filename = args.strip().strip('"\'') or "desktop.png"

        if self.dry_run:
            self.out.step("📸", f'DESKTOP_CAPTURE "{filename}" (dry-run)')
            self.results.append(
                StepResult(name=f'DESKTOP_CAPTURE "{filename}"', status=StepStatus.PASSED),
            )
            return

        try:
            self._desktop().screenshot(filename)
        except RuntimeError as exc:
            self.out.fail(f"DESKTOP_CAPTURE error: {exc}")
            self.results.append(
                StepResult(
                    name=f'DESKTOP_CAPTURE "{filename}"',
                    status=StepStatus.ERROR,
                    message=str(exc),
                ),
            )
            return

        self.out.step("📸", f'DESKTOP_CAPTURE → "{filename}"')
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
