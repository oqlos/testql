"""DDL parsing — `CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX`.

Phase 2 ships:
    * a regex-based fast path that extracts table/column/type triples from
      simple `CREATE TABLE` statements (works without sqlglot);
    * an optional sqlglot-backed parser that produces a richer `ParsedDDL`
      with constraints when sqlglot is available.

Adapters can call `parse_ddl()` and get the best result available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .dialect_resolver import has_sqlglot, normalize_dialect


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name, "type": self.type, "nullable": self.nullable,
            "primary_key": self.primary_key, "unique": self.unique,
            "default": self.default,
        }


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)

    def column(self, name: str) -> Optional[Column]:
        for c in self.columns:
            if c.name.lower() == name.lower():
                return c
        return None

    def to_dict(self) -> dict:
        return {"name": self.name, "columns": [c.to_dict() for c in self.columns]}


@dataclass
class ParsedDDL:
    tables: list[Table] = field(default_factory=list)

    def table(self, name: str) -> Optional[Table]:
        for t in self.tables:
            if t.name.lower() == name.lower():
                return t
        return None

    def to_dict(self) -> dict:
        return {"tables": [t.to_dict() for t in self.tables]}


# ── Regex fallback ──────────────────────────────────────────────────────────

# Matches `CREATE TABLE name (` — body is captured with a balanced-parens scan.
_CREATE_TABLE_HEAD_RE = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"`]?(?P<name>[A-Za-z_][\w]*)[\"`]?\s*\(",
    re.IGNORECASE,
)
# Single column line: `name TYPE [NOT NULL] [PRIMARY KEY] [UNIQUE] [DEFAULT x]`
_COLUMN_RE = re.compile(
    r"^\s*[\"`]?(?P<name>[A-Za-z_][\w]*)[\"`]?\s+"
    r"(?P<type>[A-Za-z_][\w]*(?:\s*\([^)]*\))?)"
    r"(?P<rest>.*)$",
    re.IGNORECASE,
)


def _scan_balanced_parens(sql: str, start: int) -> Optional[str]:
    """Return the substring from `start` up to the matching closing paren.

    Assumes one level of nesting is already opened (i.e. caller's regex matched
    `(`). Returns `None` if no balanced close is found.
    """
    depth = 1
    i = start
    while i < len(sql):
        ch = sql[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return sql[start:i]
        i += 1
    return None


def _iter_create_tables(sql: str):
    """Yield (table_name, body_text) for each CREATE TABLE statement."""
    for m in _CREATE_TABLE_HEAD_RE.finditer(sql):
        body = _scan_balanced_parens(sql, m.end())
        if body is not None:
            yield m.group("name"), body


def _depth_delta(ch: str) -> int:
    if ch == "(":
        return 1
    if ch == ")":
        return -1
    return 0


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body on commas that are *not* inside parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in body:
        depth += _depth_delta(ch)
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


def _parse_column_line(line: str) -> Optional[Column]:
    """Parse a single column definition; ignore standalone constraints."""
    upper = line.upper().lstrip()
    if upper.startswith(("PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK", "CONSTRAINT")):
        return None
    m = _COLUMN_RE.match(line)
    if not m:
        return None
    rest = m.group("rest").upper()
    return Column(
        name=m.group("name"),
        type=m.group("type").strip(),
        nullable=("NOT NULL" not in rest),
        primary_key=("PRIMARY KEY" in rest),
        unique=("UNIQUE" in rest),
        default=_extract_default(m.group("rest")),
    )


def _extract_default(rest: str) -> Optional[str]:
    m = re.search(r"DEFAULT\s+([^,\s]+)", rest, re.IGNORECASE)
    return m.group(1) if m else None


def _parse_table_regex(name: str, body: str) -> Table:
    columns = [c for c in (_parse_column_line(p) for p in _split_top_level(body)) if c]
    return Table(name=name, columns=columns)


def _parse_ddl_regex(sql: str) -> ParsedDDL:
    tables = [_parse_table_regex(name, body) for name, body in _iter_create_tables(sql)]
    return ParsedDDL(tables=tables)


# ── sqlglot-backed enrichment ───────────────────────────────────────────────


def _parse_ddl_sqlglot(sql: str, dialect: Optional[str]) -> ParsedDDL:
    import sqlglot
    from sqlglot import exp
    parsed = sqlglot.parse(sql, read=normalize_dialect(dialect) if dialect else None)
    tables: list[Table] = []
    for stmt in parsed:
        if not isinstance(stmt, exp.Create) or stmt.kind.upper() != "TABLE":
            continue
        tables.append(_table_from_sqlglot(stmt))
    return ParsedDDL(tables=tables)


def _table_from_sqlglot(stmt) -> Table:
    from sqlglot import exp
    name = stmt.this.this.name if hasattr(stmt.this, "this") else stmt.this.name
    columns: list[Column] = []
    schema = stmt.this
    for col in schema.expressions if hasattr(schema, "expressions") else []:
        if not isinstance(col, exp.ColumnDef):
            continue
        columns.append(_column_from_sqlglot(col))
    return Table(name=name, columns=columns)


def _column_from_sqlglot(col) -> Column:
    from sqlglot import exp
    constraints = col.args.get("constraints") or []
    has = lambda kind: any(isinstance(c.kind, kind) for c in constraints)  # noqa: E731
    return Column(
        name=col.name,
        type=str(col.args.get("kind") or "").upper().strip(),
        nullable=not has(exp.NotNullColumnConstraint),
        primary_key=has(exp.PrimaryKeyColumnConstraint),
        unique=has(exp.UniqueColumnConstraint),
    )


# ── Public API ──────────────────────────────────────────────────────────────


def parse_ddl(sql: str, dialect: Optional[str] = None, prefer_sqlglot: bool = True) -> ParsedDDL:
    """Parse one or more `CREATE TABLE` statements from `sql`.

    Uses sqlglot when available and `prefer_sqlglot` is True; otherwise falls
    back to the regex parser. The two paths produce IR-compatible outputs.
    """
    if prefer_sqlglot and has_sqlglot():
        try:
            return _parse_ddl_sqlglot(sql, dialect)
        except Exception:
            # sqlglot may fail on partial / non-standard DDL; fall back.
            pass
    return _parse_ddl_regex(sql)


__all__ = ["Column", "Table", "ParsedDDL", "parse_ddl"]
