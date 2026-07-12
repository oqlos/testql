"""testql.sql_schema — SQL DDL parsing and dialect resolution.

Regex-fast-path DDL parsing (optionally AST-level via `sqlglot`) and dialect
normalisation/transpilation, used by the core meta coverage analyzer and the
`sql2testql` plugin. Lives in core (not in the plugin) because analysing SQL
coverage must work without the adapter installed.
"""

from __future__ import annotations

from .ddl_parser import Column, ParsedDDL, Table, parse_ddl
from .dialect_resolver import (
    DEFAULT_DIALECT,
    SUPPORTED_DIALECTS,
    SqlglotMissing,
    has_sqlglot,
    is_supported,
    normalize_dialect,
    transpile,
)

__all__ = [
    "Column", "Table", "ParsedDDL", "parse_ddl",
    "DEFAULT_DIALECT", "SUPPORTED_DIALECTS", "SqlglotMissing",
    "has_sqlglot", "is_supported", "normalize_dialect", "transpile",
]
