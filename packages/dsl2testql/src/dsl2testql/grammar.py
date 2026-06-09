"""Text DSL → dict."""

from __future__ import annotations

import shlex
from typing import Any


def split_command(line: str) -> list[str]:
    line = line.strip()
    if not line or line.startswith("#"):
        return []
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return line.split()


def pick_flag(tokens: list[str], flag: str) -> str | None:
    if flag in tokens:
        idx = tokens.index(flag)
        if idx + 1 < len(tokens):
            return tokens[idx + 1]
    return None


def _parse_query(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["target"] = rest[0] if rest else ""
    if file_flag := pick_flag(rest, "FILE"):
        cmd["file"] = file_flag
    if fmt_flag := pick_flag(rest, "FORMAT"):
        cmd["format"] = fmt_flag.lower()


def _parse_patch(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["target"] = rest[0] if rest else ""
    if with_flag := pick_flag(rest, "WITH"):
        cmd["with_path"] = with_flag
    if file_flag := pick_flag(rest, "FILE"):
        cmd["file"] = file_flag


def _parse_generate(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["text"] = rest[0].strip('"').strip("'") if rest else ""
    if out_flag := pick_flag(rest, "OUT"):
        cmd["out"] = out_flag


_VERB_PARSERS = {
    "QUERY": _parse_query,
    "VALIDATE": lambda rest, cmd: cmd.update({"path": rest[0] if rest else ""}),
    "PATCH": _parse_patch,
    "GENERATE": _parse_generate,
}


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb = tokens[0].upper()
    rest = tokens[1:]
    cmd: dict[str, Any] = {"verb": verb}
    parser = _VERB_PARSERS.get(verb)
    if parser is not None:
        parser(rest, cmd)
    else:
        cmd["args"] = rest
    return cmd


def to_text(cmd: dict[str, Any]) -> str:
    verb = str(cmd.get("verb", "")).upper()
    parts = [verb]
    for key in ("target", "path", "text"):
        if val := cmd.get(key):
            parts.append(f'"{val}"' if " " in str(val) else str(val))
    for key, flag in (("file", "FILE"), ("format", "FORMAT"), ("with_path", "WITH"), ("out", "OUT")):
        if val := cmd.get(key):
            parts.extend([flag, str(val)])
    return " ".join(parts)
