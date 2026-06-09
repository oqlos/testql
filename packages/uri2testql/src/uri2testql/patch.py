"""Patch, append and update TestQL files via testql:// URIs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from uri2testql.files import resolve_testql_file
from uri2testql.query import query_uri
from uri2testql.uri import parse_testql_uri


@dataclass
class PatchResult:
    ok: bool
    uri: str
    file: str
    action: str
    selector: str = ""
    keys: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "uri": self.uri,
            "file": self.file,
            "action": self.action,
            "selector": self.selector,
            "keys": self.keys,
            "error": self.error,
        }


def _selector_pattern(parts: list[str]) -> re.Pattern[str]:
    if not parts or parts[0] == "app":
        return re.compile(r"^app\s*\{", re.MULTILINE)
    if parts[0] == "deploy":
        return re.compile(r"^deploy\s*\{", re.MULTILINE)
    if parts[0] == "entity" and len(parts) >= 2:
        name = re.escape(parts[1])
        return re.compile(rf'^entity\[name="{name}"\]\s*\{{', re.MULTILINE)
    if parts[0] == "workflow" and len(parts) >= 2:
        name = re.escape(parts[1])
        return re.compile(rf'^workflow\[name="{name}"\]\s*\{{', re.MULTILINE)
    if parts[0] == "environment" and len(parts) >= 2:
        name = re.escape(parts[1])
        return re.compile(rf'^environment\[name="{name}"\]\s*\{{', re.MULTILINE)
    if parts[0] == "interface" and len(parts) >= 2:
        iface_type = re.escape(parts[1])
        return re.compile(rf'^interface\[type="{iface_type}"\]\s*\{{', re.MULTILINE)
    raise ValueError(f"unsupported block path: {'/'.join(parts)}")


def _find_block_span(text: str, start: int) -> tuple[int, int]:
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise ValueError("unclosed block")


def replace_block_in_text(text: str, parts: list[str], new_block: str) -> str:
    pattern = _selector_pattern(parts)
    match = pattern.search(text)
    if not match:
        raise ValueError(f"block not found: {'/'.join(parts)}")
    _, end = _find_block_span(text, match.start())
    new_block = new_block.strip()
    if not new_block.endswith("\n"):
        new_block += "\n"
    return text[: match.start()] + new_block + text[end:]


def append_blocks_to_text(text: str, blocks: str) -> str:
    blocks = blocks.strip()
    if not blocks:
        return text
    if not text.endswith("\n"):
        text += "\n"
    return text + "\n" + blocks + "\n"


def patch_uri(
    uri: str,
    *,
    content: str,
    file: str | None = None,
) -> PatchResult:
    parsed = parse_testql_uri(uri)
    source = str(parsed["source"])
    parts = list(parsed["parts"])  # type: ignore[arg-type]
    file_param = file or str(parsed.get("file") or "")

    try:
        if source != "block":
            raise ValueError("patch supports testql://block/... URIs only")
        path = resolve_testql_file(file_param or None)
        text = path.read_text(encoding="utf-8")
        updated = replace_block_in_text(text, parts, content)
        path.write_text(updated, encoding="utf-8")
        query = query_uri(uri, file=str(path), fmt="less")
        return PatchResult(
            ok=True,
            uri=uri,
            file=str(path),
            action="patch",
            selector=query.selector,
            keys=query.keys,
        )
    except Exception as exc:
        return PatchResult(
            ok=False,
            uri=uri,
            file=file_param,
            action="patch",
            error=str(exc),
        )


def append_uri(
    uri: str,
    *,
    content: str,
    file: str | None = None,
) -> PatchResult:
    file_param = file or str(parse_testql_uri(uri).get("file") or "") if uri.startswith("testql://") else uri
    try:
        path = resolve_testql_file(file_param or None)
        text = path.read_text(encoding="utf-8")
        updated = append_blocks_to_text(text, content)
        path.write_text(updated, encoding="utf-8")
        return PatchResult(
            ok=True,
            uri=uri,
            file=str(path),
            action="append",
        )
    except Exception as exc:
        return PatchResult(
            ok=False,
            uri=uri,
            file=file_param,
            action="append",
            error=str(exc),
        )


def apply_uri(
    uri: str,
    *,
    dest: str | None = None,
    content: str | None = None,
    file: str | None = None,
    mode: str = "materialize",
) -> PatchResult:
    """Apply URI action: materialize, patch, append, or update (alias for patch)."""
    action = mode.lower()
    if action in {"update", "patch", "replace"}:
        if not content:
            raise ValueError("patch/update requires content")
        return patch_uri(uri, content=content, file=file)
    if action == "append":
        if not content:
            raise ValueError("append requires content")
        target = file or dest or uri
        return append_uri(target, content=content, file=file)
    if action in {"materialize", "write"}:
        from uri2testql.materialize import materialize_uri

        result = materialize_uri(uri, dest=dest)
        return PatchResult(
            ok=result.ok,
            uri=uri,
            file=result.dest,
            action="materialize",
            selector=result.selector,
            keys=result.keys,
            error=result.error,
        )
    raise ValueError(f"unsupported apply mode: {mode}")


def update_uri(
    uri: str,
    *,
    content: str,
    file: str | None = None,
) -> PatchResult:
    return patch_uri(uri, content=content, file=file)
