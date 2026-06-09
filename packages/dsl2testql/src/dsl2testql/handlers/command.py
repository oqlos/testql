"""Write command handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsl2testql.result import DslResult


def _read_content(path: str) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8")


def handle_generate(cmd: dict[str, Any], *, line: str, default_file: str | None) -> DslResult:
    from nlp2testql.pipeline import generate_spec

    generated = generate_spec(cmd.get("text", ""), out_path=cmd.get("out"), validate=True)
    return DslResult(
        ok=generated.ok,
        command=line,
        action="generate",
        output=generated.testql,
        data={
            "output_path": generated.output_path,
            "planner": generated.plan.planner,
            "validation": generated.validation,
        },
        error=generated.error,
    )


def handle_patch(cmd: dict[str, Any], *, line: str, default_file: str | None, verb: str = "patch") -> DslResult:
    from uri2testql.patch import patch_uri

    with_path = cmd.get("with_path")
    if not with_path:
        raise ValueError(f"{verb.upper()} requires WITH <fragment-file>")
    content = _read_content(with_path)
    result = patch_uri(cmd.get("target", ""), content=content, file=cmd.get("file") or default_file)
    return DslResult(
        ok=result.ok,
        command=line,
        action=verb,
        output=json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        data=result.to_dict(),
        error=result.error,
    )


def handle_from_tokens(line: str, tokens: list[str], *, default_file: str | None) -> DslResult:
    """Legacy token dispatch for engine compatibility."""
    from dsl2testql.grammar import parse_line
    from dsl2testql.handlers.query import handle_query, handle_validate

    cmd = parse_line(line)
    if cmd is None:
        return DslResult(ok=True, command=line, action="noop")
    verb = cmd["verb"]
    try:
        if verb == "QUERY":
            return handle_query(cmd, line=line, default_file=default_file)
        if verb == "VALIDATE":
            return handle_validate(cmd, line=line, default_file=default_file)
        if verb == "GENERATE":
            return handle_generate(cmd, line=line, default_file=default_file)
        if verb == "PATCH":
            return handle_patch(cmd, line=line, default_file=default_file)
        return DslResult(ok=False, command=line, action=verb.lower(), error=f"unknown command: {verb}")
    except Exception as exc:
        return DslResult(ok=False, command=line, action=verb.lower(), error=str(exc))
