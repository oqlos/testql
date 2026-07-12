"""Data models for desktop window/session state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DesktopWindow:
    id: str
    title: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    workspace: int = -1
    active: bool = False


@dataclass
class DesktopSession:
    """Tracks launched processes and last focused window."""

    launched_pids: list[int] = field(default_factory=list)
    focused_window_id: str | None = None
    focused_title: str | None = None
