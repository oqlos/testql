"""TestQL native desktop DSL catalog — metadata for env2llm / MCP / nlp2uri."""

from __future__ import annotations

from typing import Any

# (mcp_name, description, required_fields, optional_fields, oql_command)
_DESKTOP_COMMANDS: tuple[tuple[str, str, list[str], list[str], str], ...] = (
    (
        "testql_desktop_list",
        "List open desktop windows (wmctrl or xdotool)",
        [],
        [],
        "DESKTOP_LIST",
    ),
    (
        "testql_desktop_focus",
        "Focus desktop window by title substring or hex window id",
        ["target"],
        [],
        "DESKTOP_FOCUS",
    ),
    (
        "testql_desktop_launch",
        "Launch native application executable",
        ["executable"],
        ["args"],
        "DESKTOP_LAUNCH",
    ),
    (
        "testql_desktop_click",
        "Click screen coordinates (ydotool Wayland / xdotool X11)",
        ["x", "y"],
        ["button"],
        "DESKTOP_CLICK",
    ),
    (
        "testql_desktop_type",
        "Type text into focused window (wtype / xdotool)",
        ["text"],
        [],
        "DESKTOP_TYPE",
    ),
    (
        "testql_desktop_key",
        "Send key combo to focused window (Return, ctrl+s, …)",
        ["combo"],
        [],
        "DESKTOP_KEY",
    ),
    (
        "testql_desktop_capture",
        "Full-screen screenshot (grim / scrot / import)",
        ["file"],
        [],
        "DESKTOP_CAPTURE",
    ),
    (
        "testql_desktop_assert_window",
        "Assert a desktop window title exists",
        ["title"],
        [],
        "DESKTOP_ASSERT_WINDOW",
    ),
    (
        "testql_desktop_stop",
        "Terminate apps launched in this TestQL desktop session",
        [],
        [],
        "DESKTOP_STOP",
    ),
)

# Optional Python libraries for richer desktop control (not required by core backend).
RECOMMENDED_PYTHON_LIBS: tuple[dict[str, str], ...] = (
    {
        "package": "dogtail",
        "role": "semantic",
        "note": "AT-SPI wrapper — click/type by accessible name/role (GTK/Qt)",
    },
    {
        "package": "pyatspi",
        "role": "semantic",
        "note": "Low-level accessibility tree (dependency of dogtail)",
    },
    {
        "package": "pyautogui",
        "role": "fallback",
        "note": "Coordinate clicks and typing when AT-SPI unavailable",
    },
    {
        "package": "pynput",
        "role": "recorder",
        "note": "Record mouse/keyboard sessions → generate TestQL scenarios",
    },
    {
        "package": "opencv-python",
        "role": "vision",
        "note": "Image/template matching for UI without accessibility API",
    },
    {
        "package": "mss",
        "role": "vision",
        "note": "Fast screenshots for CV-based assertions",
    },
    {
        "package": "pywinauto",
        "role": "windows",
        "note": "Windows UI Automation (cross-platform CI on Win)",
    },
    {
        "package": "playwright",
        "role": "web",
        "note": "Browser/Electron webview DOM — use GUI_* commands, not DESKTOP_*",
    },
)


def collect_desktop_catalog() -> dict[str, Any]:
    """Return desktop DSL + host-tool metadata for registry/MCP consumers."""
    from testql.desktop.backend import detect_display_server
    import shutil

    host_tools = [
        name
        for name in ("wmctrl", "xdotool", "wtype", "ydotool", "grim", "scrot", "import")
        if shutil.which(name)
    ]
    return {
        "display_server": detect_display_server(),
        "host_tools": host_tools,
        "commands": [
            {
                "name": name,
                "description": description,
                "required": required,
                "optional": optional,
                "oql_command": oql,
            }
            for name, description, required, optional, oql in _DESKTOP_COMMANDS
        ],
        "recommended_python_libs": list(RECOMMENDED_PYTHON_LIBS),
    }
