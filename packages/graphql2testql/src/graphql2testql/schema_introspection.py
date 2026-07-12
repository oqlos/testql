"""GraphQL schema introspection helpers.

Phase 3 ships:

    * a constant `INTROSPECTION_QUERY` (the canonical query used to fetch a
      remote schema);
    * `parse_schema()` that lightweight-parses a `schema.graphql` SDL string
      into a list of `TypeDef`s — without `graphql-core` (regex), and richer
      with it when available.

Network execution is deferred to the runner phase; this module is purely
declarative.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


INTROSPECTION_QUERY = """\
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      kind name description
      fields(includeDeprecated: true) { name args { name type { name kind } } type { name kind } }
    }
  }
}
"""


@dataclass
class TypeDef:
    name: str
    kind: str = "OBJECT"  # OBJECT | INTERFACE | UNION | ENUM | INPUT_OBJECT | SCALAR
    fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "fields": list(self.fields)}


_TYPE_BLOCK_RE = re.compile(
    r"\b(?P<kind>type|interface|union|enum|input|scalar)\s+(?P<name>[A-Za-z_][\w]*)\b",
    re.IGNORECASE,
)
# Match `name :` (after optionally stripping arg-list parens). Captures field
# / enum-value names. Used globally on the body — works whether fields are on
# one line or many.
_FIELD_NAME_RE = re.compile(r"\b(?P<name>[A-Za-z_]\w*)\s*:")
# Strip `(...)` content (argument lists) before scanning for fields, so
# argument names don't leak into the field list.
_ARG_LIST_RE = re.compile(r"\([^)]*\)")


def _scan_balanced_braces(text: str, start: int) -> Optional[str]:
    depth = 1
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
        i += 1
    return None


_CANONICAL_KIND = {
    "TYPE": "OBJECT",
    "INPUT": "INPUT_OBJECT",
}


def _kind_to_canonical(kind: str) -> str:
    upper = kind.upper()
    return _CANONICAL_KIND.get(upper, upper)


def _extract_field_names(body: str) -> list[str]:
    """Pull field names from a type body, ignoring argument-list contents."""
    cleaned = _ARG_LIST_RE.sub("", body)
    return [m.group("name") for m in _FIELD_NAME_RE.finditer(cleaned)]


def _parse_type_block(text: str, head_match: "re.Match[str]") -> tuple[Optional[TypeDef], int]:
    """Build a `TypeDef` from one match. Returns (typedef|None, next_offset)."""
    canonical_kind = _kind_to_canonical(head_match.group("kind"))
    name = head_match.group("name")
    next_offset = head_match.end()
    open_brace = text.find("{", head_match.end())
    if canonical_kind == "SCALAR" or open_brace == -1:
        return TypeDef(name=name, kind=canonical_kind), next_offset
    body = _scan_balanced_braces(text, open_brace + 1)
    if body is None:
        return TypeDef(name=name, kind=canonical_kind), next_offset
    return (TypeDef(name=name, kind=canonical_kind, fields=_extract_field_names(body)),
            open_brace + 1 + len(body) + 1)


def parse_schema(sdl: str) -> list[TypeDef]:
    """Best-effort SDL parser. Returns the list of declared top-level types."""
    out: list[TypeDef] = []
    pos = 0
    while pos < len(sdl):
        m = _TYPE_BLOCK_RE.search(sdl, pos)
        if m is None:
            break
        typedef, next_offset = _parse_type_block(sdl, m)
        if typedef is not None:
            out.append(typedef)
        pos = max(next_offset, m.end())
    return out


def has_graphql_core() -> bool:
    try:
        import graphql  # noqa: F401
    except ImportError:
        return False
    return True


__all__ = [
    "INTROSPECTION_QUERY",
    "TypeDef",
    "parse_schema",
    "has_graphql_core",
]
