"""Query (DML) classification + sqlglot-backed analysis.

The fast path classifies a statement as `select | insert | update | delete | other`
using a leading-keyword regex. When sqlglot is installed, `analyze_query()`
returns a richer `QueryInfo` with referenced tables, column projections, and a
re-formatted SQL string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .dialect_resolver import has_sqlglot, normalize_dialect

_LEADING_KEYWORD_RE = re.compile(r"^\s*([A-Za-z]+)", re.MULTILINE)

_KIND_BY_KEYWORD = {
    "SELECT": "select",
    "WITH": "select",  # CTE
    "INSERT": "insert",
    "UPDATE": "update",
    "DELETE": "delete",
    "MERGE": "merge",
    "REPLACE": "insert",
}


@dataclass
class QueryInfo:
    kind: str = "other"          # select | insert | update | delete | merge | other
    raw: str = ""
    tables: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    formatted: Optional[str] = None  # sqlglot-pretty-printed (when available)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind, "raw": self.raw,
            "tables": list(self.tables), "columns": list(self.columns),
            "formatted": self.formatted,
        }


def classify(sql: str) -> str:
    """Return the canonical kind of `sql` from its leading keyword."""
    m = _LEADING_KEYWORD_RE.search(sql)
    if not m:
        return "other"
    return _KIND_BY_KEYWORD.get(m.group(1).upper(), "other")


def _analyze_with_sqlglot(sql: str, dialect: Optional[str]) -> QueryInfo:
    import sqlglot
    from sqlglot import exp
    tree = sqlglot.parse_one(sql, read=normalize_dialect(dialect) if dialect else None)
    tables = sorted({t.name for t in tree.find_all(exp.Table) if t.name})
    columns = _projection_columns(tree)
    return QueryInfo(
        kind=classify(sql),
        raw=sql,
        tables=tables,
        columns=columns,
        formatted=tree.sql(dialect=normalize_dialect(dialect) if dialect else None),
    )


def _projection_columns(tree) -> list[str]:
    """Best-effort extraction of selected/referenced column names."""
    from sqlglot import exp
    cols: list[str] = []
    for col in tree.find_all(exp.Column):
        cols.append(col.name)
    # de-dupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for c in cols:
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out


def analyze_query(sql: str, dialect: Optional[str] = None) -> QueryInfo:
    """Analyse `sql`. Falls back to a kind-only `QueryInfo` when sqlglot is missing."""
    if has_sqlglot():
        try:
            return _analyze_with_sqlglot(sql, dialect)
        except Exception:
            pass
    return QueryInfo(kind=classify(sql), raw=sql)


__all__ = ["QueryInfo", "classify", "analyze_query"]
