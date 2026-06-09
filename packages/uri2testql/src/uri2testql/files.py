"""Resolve TestQL file path from URI params or cwd."""

from __future__ import annotations

from pathlib import Path


def resolve_testql_file(file_param: str | None = None, *, start: Path | None = None) -> Path:
    if file_param:
        path = Path(file_param).expanduser()
        if not path.is_absolute():
            base = start or Path.cwd()
            path = (base / path).resolve()
        else:
            path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"TestQL file not found: {path}")
        return path

    base = start or Path.cwd()
    for name in ("app.testql.less", "app.doql.less"):
        candidate = base / name
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError("No app.testql.less or app.doql.less found in current directory")
