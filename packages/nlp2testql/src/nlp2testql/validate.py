"""Validate TestQL manifest files and content."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from testql.doql_parser import DoqlParser


def validate_testql(content: str) -> dict[str, Any]:
    try:
        parser = DoqlParser()
        parser.parse(content)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def validate_testql_file(path: str | Path) -> dict[str, Any]:
    try:
        parser = DoqlParser()
        parser.parse_file(Path(path))
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
