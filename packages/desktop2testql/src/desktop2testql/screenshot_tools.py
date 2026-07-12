"""Screenshot candidate builders and runners for LinuxDesktopBackend."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

RunFn = Callable[..., subprocess.CompletedProcess[str]]


def screenshot_candidates(
    *,
    display_server: str,
    output: Path,
) -> list[tuple[list[str], dict[str, str] | None, float]]:
    candidates: list[tuple[list[str], dict[str, str] | None, float]] = []
    if display_server == "wayland":
        x_display = os.environ.get("DISPLAY")
        if x_display and shutil.which("scrot"):
            candidates.append((["scrot", str(output)], {"DISPLAY": x_display}, 10.0))
        if shutil.which("grim"):
            candidates.append((["grim", str(output)], None, 10.0))
    else:
        if shutil.which("scrot"):
            candidates.append((["scrot", str(output)], None, 10.0))
        if shutil.which("gnome-screenshot"):
            candidates.append((["gnome-screenshot", "-f", str(output)], None, 8.0))
    if shutil.which("import"):
        candidates.append((["import", "-window", "root", str(output)], None, 10.0))
    return candidates


def try_screenshot_candidates(
    candidates: list[tuple[list[str], dict[str, str] | None, float]],
    *,
    output: Path,
    run_fn: RunFn,
    is_blank: Callable[[Path], bool],
) -> list[str]:
    errors: list[str] = []
    for argv, run_env, timeout in candidates:
        if not shutil.which(argv[0]):
            continue
        try:
            proc = run_fn(argv, env=run_env, timeout=timeout)
        except subprocess.TimeoutExpired:
            errors.append(f"{argv[0]}: timeout after {timeout}s")
            continue
        except OSError as exc:
            errors.append(f"{argv[0]}: {exc}")
            continue
        if proc.returncode == 0 and output.is_file() and output.stat().st_size > 0:
            if not is_blank(output):
                return errors
            errors.append(f"{argv[0]}: blank capture")
            continue
        detail = (proc.stderr or proc.stdout or "").strip() or f"{argv[0]} failed"
        errors.append(f"{argv[0]}: {detail}")
    return errors
