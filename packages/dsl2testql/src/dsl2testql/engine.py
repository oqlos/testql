"""TestQL control DSL — backward compatibility shim."""

from __future__ import annotations

from dsl2testql.bus import dispatch as _dispatch, execute_dsl as _execute_dsl, execute_dsl_line as _execute_dsl_line
from dsl2testql.result import DslResult

__all__ = ["DslResult", "execute_dsl", "execute_dsl_line", "dispatch"]


def execute_dsl_line(line: str, *, default_file: str | None = None) -> DslResult:
    return _execute_dsl_line(line, default_file=default_file)


def execute_dsl(text: str, *, default_file: str | None = None) -> list[DslResult]:
    return _execute_dsl(text, default_file=default_file)


def dispatch(
    envelope: str | dict | bytes,
    *,
    default_file: str | None = None,
) -> DslResult:
    return _dispatch(envelope, default_file=default_file)
