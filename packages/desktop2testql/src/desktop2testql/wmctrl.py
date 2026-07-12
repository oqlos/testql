"""Parse wmctrl window listings."""

from __future__ import annotations

import re

from desktop2testql.models import DesktopWindow

_WMCTRL_LINE_RE = re.compile(
    r"^(0x[0-9a-fA-F]+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+\S+\s+(.+)$"
)


def parse_wmctrl_listing(text: str) -> list[DesktopWindow]:
    windows: list[DesktopWindow] = []
    for line in text.splitlines():
        match = _WMCTRL_LINE_RE.match(line.strip())
        if not match:
            continue
        window_id, workspace, x, y, width, height, title = match.groups()
        windows.append(
            DesktopWindow(
                id=window_id,
                title=title.strip(),
                x=int(x),
                y=int(y),
                width=int(width),
                height=int(height),
                workspace=int(workspace),
            ),
        )
    return windows
