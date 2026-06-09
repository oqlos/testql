"""Helpers for expanding TestTOON GUI tables into OQL GUI_* commands."""

from __future__ import annotations

from typing import Callable

from ._parser import OqlLine

_NAV_ACTIONS = frozenset({"open", "start", "navigate", "goto"})
_INPUT_ACTIONS = frozenset({"input", "type", "fill"})
_VISIBLE_ACTIONS = frozenset({"assert_visible", "visible"})
_TEXT_ACTIONS = frozenset({"assert_text", "text"})
_STOP_ACTIONS = frozenset({"stop", "close"})
_SKIP_WAIT = frozenset({None, "-", "", 0, "0"})

AppendFn = Callable[[list[OqlLine], int, str, str], int]


def quote_gui_token(token: str, *, empty: str = '""') -> str:
    if not token:
        return empty
    if token.startswith("${"):
        return token
    return f'"{token}"'


def gui_row_fields(row: dict[str, object]) -> tuple[str, str, object, object]:
    action = str(row.get("action", "")).strip().lower()
    selector = str(row.get("selector") or row.get("target") or "").strip()
    value = row.get("value") if row.get("value") not in (None, "-") else row.get("text")
    wait_ms = row.get("wait_ms")
    return action, selector, value, wait_ms


def _format_gui_value(value: object | None) -> str:
    if value is not None and str(value).startswith("${"):
        return str(value)
    if value is not None:
        return f'"{value}"'
    return "None"


def _format_gui_expected(value: object | None) -> str:
    expected = value if value is not None else ""
    if expected != "" and str(expected).startswith("${"):
        return str(expected)
    return quote_gui_token(str(expected)) if expected != "" else ""


def _gui_action_group(action: str) -> str:
    if action in _NAV_ACTIONS:
        return "nav"
    if action in _INPUT_ACTIONS:
        return "input"
    if action == "click":
        return "click"
    if action in _VISIBLE_ACTIONS:
        return "visible"
    if action in _TEXT_ACTIONS:
        return "text"
    if action in _STOP_ACTIONS:
        return "stop"
    if action:
        return "custom"
    return "none"


def _expand_gui_nav(
    *,
    selector: str,
    value: object | None,
    session_open: bool,
    lines: list[OqlLine],
    line_num: int,
    append: AppendFn,
) -> tuple[int, bool]:
    target = str(value or selector or "${target_url}")
    command = "GUI_NAVIGATE" if session_open else "GUI_START"
    line_num = append(lines, line_num, command, quote_gui_token(target))
    return line_num, True


def _expand_gui_input(
    *,
    selector: str,
    value: object | None,
    lines: list[OqlLine],
    line_num: int,
    append: AppendFn,
) -> int:
    return append(
        lines,
        line_num,
        "GUI_INPUT",
        f"{quote_gui_token(selector)} {_format_gui_value(value)}",
    )


def _expand_gui_text(
    *,
    selector: str,
    value: object | None,
    lines: list[OqlLine],
    line_num: int,
    append: AppendFn,
) -> int:
    args = f"{quote_gui_token(selector)} {_format_gui_expected(value)}".strip()
    return append(lines, line_num, "GUI_ASSERT_TEXT", args)


def _expand_gui_custom(
    *,
    action: str,
    selector: str,
    value: object | None,
    lines: list[OqlLine],
    line_num: int,
    append: AppendFn,
) -> int:
    sel = quote_gui_token(selector)
    val = quote_gui_token(str(value) if value is not None else "")
    return append(lines, line_num, action.upper(), f"{sel} {val}".strip())


def expand_gui_row(
    row: dict[str, object],
    *,
    lines: list[OqlLine],
    line_num: int,
    session_open: bool,
    append: AppendFn,
) -> tuple[int, bool]:
    action, selector, value, wait_ms = gui_row_fields(row)
    group = _gui_action_group(action)

    if group == "nav":
        line_num, session_open = _expand_gui_nav(
            selector=selector,
            value=value,
            session_open=session_open,
            lines=lines,
            line_num=line_num,
            append=append,
        )
    elif group == "input":
        line_num = _expand_gui_input(
            selector=selector,
            value=value,
            lines=lines,
            line_num=line_num,
            append=append,
        )
    elif group == "click":
        line_num = append(lines, line_num, "GUI_CLICK", quote_gui_token(selector))
    elif group == "visible":
        line_num = append(lines, line_num, "GUI_ASSERT_VISIBLE", quote_gui_token(selector))
    elif group == "text":
        line_num = _expand_gui_text(
            selector=selector,
            value=value,
            lines=lines,
            line_num=line_num,
            append=append,
        )
    elif group == "stop":
        line_num = append(lines, line_num, "GUI_STOP", "")
        session_open = False
    elif group == "custom":
        line_num = _expand_gui_custom(
            action=action,
            selector=selector,
            value=value,
            lines=lines,
            line_num=line_num,
            append=append,
        )

    if wait_ms not in _SKIP_WAIT:
        line_num = append(lines, line_num, "WAIT", str(wait_ms))
    return line_num, session_open
