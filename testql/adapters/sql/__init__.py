"""testql.adapters.sql — SQL contract adapter (Phase 2).

Optional `sqlglot` dependency: install via `pip install testql[sql]` to enable
AST-level DDL parsing, query analysis, and dialect transpilation. The adapter
itself works without sqlglot using a regex fast path.
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
from .fixtures import ConnectionFixture, SchemaFixture, schema_fixture_from_rows
from .query_parser import QueryInfo, analyze_query, classify
from .sql_adapter import SqlDSLAdapter, parse, render

__all__ = [
    # Adapter
    "SqlDSLAdapter",
    "parse",
    "render",
    # Dialect resolution
    "DEFAULT_DIALECT",
    "SUPPORTED_DIALECTS",
    "SqlglotMissing",
    "has_sqlglot",
    "is_supported",
    "normalize_dialect",
    "transpile",
    # DDL parsing
    "Column",
    "Table",
    "ParsedDDL",
    "parse_ddl",
    # Query parsing
    "QueryInfo",
    "classify",
    "analyze_query",
    # Fixtures
    "ConnectionFixture",
    "SchemaFixture",
    "schema_fixture_from_rows",
]
