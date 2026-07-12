"""Query syntax helpers for GraphQL.

Network execution is intentionally out of scope for Phase 3 (it belongs to the
runner phase). This module only provides the pieces that don't need a live
endpoint: classification of query strings and best-effort parsing of inline
variable maps.
"""

from __future__ import annotations

import re
from typing import Any


_OP_PREFIX_RE = re.compile(r"^\s*(?P<op>query|mutation|subscription)\b", re.IGNORECASE)
_INLINE_PAIR_RE = re.compile(
    r"\s*(?P<key>[A-Za-z_][\w]*)\s*:\s*(?P<value>"
    r"\"[^\"]*\"|'[^']*'|true|false|null|-?\d+\.?\d*|[A-Za-z_][\w]*"
    r")\s*,?"
)


def classify_operation(body: str) -> str:
    """Return `query` | `mutation` | `subscription` | `query` (default)."""
    m = _OP_PREFIX_RE.match(body or "")
    if not m:
        return "query"
    return m.group("op").lower()


def parse_variables(text: str | None) -> dict[str, Any]:
    """Parse a TestTOON-friendly variable map like `{id: '42', limit: 10}`.

    Accepts both JSON-ish syntax and bare keys. Returns `{}` when input is
    empty/None or unparseable.
    """
    if not text:
        return {}
    blob = text.strip()
    if not blob:
        return {}
    if blob.startswith("{") and blob.endswith("}"):
        blob = blob[1:-1]
    out: dict[str, Any] = {}
    for m in _INLINE_PAIR_RE.finditer(blob):
        out[m.group("key")] = _coerce_literal(m.group("value"))
    return out


_LITERAL_KEYWORDS: dict[str, Any] = {"true": True, "false": False, "null": None}


def _try_number(raw: str) -> Any:
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _is_quoted(raw: str) -> bool:
    return len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}


def _coerce_literal(raw: str) -> Any:
    if raw in _LITERAL_KEYWORDS:
        return _LITERAL_KEYWORDS[raw]
    if _is_quoted(raw):
        return raw[1:-1]
    return _try_number(raw)


__all__ = ["classify_operation", "parse_variables"]
