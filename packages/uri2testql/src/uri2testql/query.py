"""Query addressed blocks from TestQL manifests."""

from __future__ import annotations

import io
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

import yaml
from testql.doql_parser import DoqlParser

from uri2testql.block_resolver import (
    extract_block_data,
    parse_block_ref,
    render_block_partial,
    selector_from_ref,
)
from uri2testql.files import resolve_testql_file
from uri2testql.uri import parse_testql_uri


@dataclass
class QueryResult:
    ok: bool
    uri: str
    selector: str
    file: str
    data: Any = None
    rendered: str = ""
    format: str = "json"
    error: str | None = None
    keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "uri": self.uri,
            "selector": self.selector,
            "file": self.file,
            "data": self.data,
            "rendered": self.rendered,
            "format": self.format,
            "keys": self.keys,
            "error": self.error,
        }


def _to_plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _to_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    return value


def _render_partial(spec: Any, parts: list[str]) -> str:
    return render_block_partial(spec, parse_block_ref(parts))


def _extract_data(spec: Any, parts: list[str]) -> Any:
    return extract_block_data(spec, parse_block_ref(parts), _to_plain)


def _selector_from_parts(parts: list[str]) -> str:
    try:
        return selector_from_ref(parse_block_ref(parts))
    except ValueError:
        return "/".join(parts)


def _apply_output_format(result: QueryResult, output_fmt: str, *, less_rendered: str) -> QueryResult:
    if output_fmt == "yaml":
        result.rendered = yaml.safe_dump(result.data, sort_keys=False, allow_unicode=True)
    elif output_fmt == "json":
        result.rendered = json.dumps(result.data, ensure_ascii=False, indent=2)
    else:
        result.rendered = less_rendered
    return result


def _query_file_source(
    uri: str,
    *,
    parts: list[str],
    file_param: str,
    output_fmt: str,
) -> QueryResult:
    path = resolve_testql_file(parts[0] if parts else file_param or None)
    parser = DoqlParser()
    spec = parser.parse_file(path)
    data = _to_plain(spec)
    keys = sorted(data.keys()) if isinstance(data, dict) else []
    return QueryResult(
        ok=True,
        uri=uri,
        selector=str(path),
        file=str(path),
        data=data,
        rendered=path.read_text(encoding="utf-8"),
        format=output_fmt,
        keys=keys,
    )


def _query_generate_source(uri: str, *, parsed: dict[str, object]) -> QueryResult:
    prompt = str(parsed.get("prompt") or "")
    if not prompt:
        raise ValueError("testql://generate requires ?prompt=...")
    try:
        from nlp2testql.pipeline import generate_spec
    except ImportError as exc:
        raise RuntimeError("nlp2testql required") from exc
    generated = generate_spec(prompt, validate=True)
    if not generated.ok:
        raise RuntimeError(generated.error or "generation failed")
    return QueryResult(
        ok=True,
        uri=uri,
        selector="generate",
        file="",
        data={"prompt": prompt},
        rendered=generated.testql,
        format="less",
        keys=["prompt"],
    )


def _query_block_source(
    uri: str,
    *,
    parts: list[str],
    file_param: str,
    output_fmt: str,
) -> QueryResult:
    path = resolve_testql_file(file_param or None)
    spec = DoqlParser().parse_file(path)
    data = _extract_data(spec, parts)
    rendered = _render_partial(spec, parts)
    keys = sorted(data.keys()) if isinstance(data, dict) else []
    result = QueryResult(
        ok=True,
        uri=uri,
        selector=_selector_from_parts(parts),
        file=str(path),
        data=data,
        rendered=rendered,
        format=output_fmt,
        keys=keys,
    )
    return _apply_output_format(result, output_fmt, less_rendered=rendered)


def query_uri(uri: str, *, file: str | None = None, fmt: str | None = None) -> QueryResult:
    parsed = parse_testql_uri(uri)
    source = str(parsed["source"])
    parts = list(parsed["parts"])  # type: ignore[arg-type]
    file_param = file or str(parsed.get("file") or "")
    output_fmt = (fmt or str(parsed.get("format") or "json")).lower()

    try:
        if source == "file":
            return _query_file_source(uri, parts=parts, file_param=file_param, output_fmt=output_fmt)
        if source == "generate":
            return _query_generate_source(uri, parsed=parsed)
        if source == "block":
            return _query_block_source(uri, parts=parts, file_param=file_param, output_fmt=output_fmt)
        raise ValueError(f"unsupported testql source: {source}")
    except Exception as exc:
        return QueryResult(
            ok=False,
            uri=uri,
            selector=_selector_from_parts(parts),
            file=file_param,
            format=output_fmt,
            error=str(exc),
        )
