"""Materialize testql:// URIs into files or partial specs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from uri2testql.files import resolve_testql_file
from uri2testql.query import query_uri
from uri2testql.uri import parse_testql_uri


@dataclass
class MaterializeResult:
    ok: bool
    uri: str
    dest: str
    selector: str = ""
    keys: list[str] = field(default_factory=list)
    source: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "uri": self.uri,
            "dest": self.dest,
            "selector": self.selector,
            "keys": self.keys,
            "source": self.source,
            "error": self.error,
        }


def _materialize_file(uri: str, *, parts: list[str], target: str) -> MaterializeResult:
    src = resolve_testql_file(parts[0] if parts else None)
    out = Path(target).expanduser().resolve() if target else src
    if target:
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    return MaterializeResult(
        ok=True,
        uri=uri,
        dest=str(out),
        selector=str(src),
        source=f"file:{src}",
    )


def _materialize_generate(uri: str, *, parsed: dict[str, object], target: str) -> MaterializeResult:
    dest = target or "app.testql.less"
    try:
        from nlp2testql.pipeline import generate_spec
    except ImportError as exc:
        raise RuntimeError("nlp2testql required") from exc
    prompt = str(parsed.get("prompt") or "")
    generated = generate_spec(prompt, out_path=dest, validate=True)
    if not generated.ok:
        raise RuntimeError(generated.error or "generation failed")
    return MaterializeResult(
        ok=True,
        uri=uri,
        dest=str(Path(dest).resolve()),
        selector="generate",
        keys=["prompt"],
        source="nlp2testql",
    )


def _materialize_block(uri: str, *, params: dict[str, object], target: str) -> MaterializeResult:
    if not target:
        raise ValueError("block materialize requires --dest or ?dest=")
    fmt = str(params.get("format") or "less")
    query = query_uri(uri, fmt=fmt)
    if not query.ok:
        raise RuntimeError(query.error or "query failed")
    out = Path(target).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(query.rendered, encoding="utf-8")
    return MaterializeResult(
        ok=True,
        uri=uri,
        dest=str(out),
        selector=query.selector,
        keys=query.keys,
        source=f"block:{query.file}",
    )


def materialize_uri(uri: str, *, dest: str | None = None) -> MaterializeResult:
    parsed = parse_testql_uri(uri)
    source = str(parsed["source"])
    parts = list(parsed["parts"])  # type: ignore[arg-type]
    params = parsed["params"]
    assert isinstance(params, dict)
    target = dest or str(parsed.get("dest") or "")

    try:
        if source == "file":
            return _materialize_file(uri, parts=parts, target=target)
        if source == "generate":
            return _materialize_generate(uri, parsed=parsed, target=target)
        if source == "block":
            return _materialize_block(uri, params=params, target=target)
        raise ValueError(f"unsupported testql source: {source}")
    except Exception as exc:
        return MaterializeResult(ok=False, uri=uri, dest=target or "", error=str(exc))
