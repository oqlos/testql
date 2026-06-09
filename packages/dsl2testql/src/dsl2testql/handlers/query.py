"""Read-only query handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsl2testql.result import DslResult


def handle_query(cmd: dict[str, Any], *, line: str, default_file: str | None) -> DslResult:
    from uri2testql.query import query_uri

    uri = cmd.get("target", "")
    file_param = cmd.get("file") or default_file
    fmt = (cmd.get("format") or "json").lower()
    result = query_uri(uri, file=file_param, fmt=fmt)
    return DslResult(
        ok=result.ok,
        command=line,
        action="query",
        output=result.rendered or json.dumps(result.data, ensure_ascii=False, indent=2),
        data=result.to_dict(),
        error=result.error,
    )


def handle_validate(cmd: dict[str, Any], *, line: str, default_file: str | None) -> DslResult:
    from nlp2testql.validate import validate_testql_file

    path = cmd.get("path") or default_file or "app.testql.less"
    result = validate_testql_file(path)
    return DslResult(
        ok=bool(result.get("ok")),
        command=line,
        action="validate",
        output=json.dumps(result, ensure_ascii=False, indent=2),
        data=result,
        error=None if result.get("ok") else str(result.get("errors") or result.get("error")),
    )
