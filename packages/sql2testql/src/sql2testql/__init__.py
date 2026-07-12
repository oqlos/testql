"""sql2testql — SQL contract adapter plugin for TestQL.

Registers the `sql` DSL adapter via the `testql.plugins` entry point and the
`sql` generator source via the `testql.sources` entry point. Optional
`sqlglot` dependency: install via `pip install sql2testql[sqlglot]` for
AST-level DDL parsing, query analysis, and dialect transpilation — the
adapter itself works without it using the regex fast path from
`testql.sql_schema`.
"""

from __future__ import annotations

from testql.sql_schema import (
    DEFAULT_DIALECT,
    SUPPORTED_DIALECTS,
    Column,
    ParsedDDL,
    SqlglotMissing,
    Table,
    has_sqlglot,
    is_supported,
    normalize_dialect,
    parse_ddl,
    transpile,
)

from .adapter import SqlDSLAdapter, parse, render
from .fixtures import ConnectionFixture, SchemaFixture, schema_fixture_from_rows
from .query_parser import QueryInfo, analyze_query, classify


def register_testql_plugin(registry) -> None:
    """`testql.plugins` entry-point hook — see `AdapterRegistry.load_plugins`."""
    registry.register(SqlDSLAdapter())


__all__ = [
    # Adapter
    "SqlDSLAdapter", "parse", "render",
    # Dialect resolution (re-exported from testql.sql_schema)
    "DEFAULT_DIALECT", "SUPPORTED_DIALECTS", "SqlglotMissing",
    "has_sqlglot", "is_supported", "normalize_dialect", "transpile",
    # DDL parsing (re-exported from testql.sql_schema)
    "Column", "Table", "ParsedDDL", "parse_ddl",
    # Fixtures
    "ConnectionFixture", "SchemaFixture", "schema_fixture_from_rows",
    # Query analysis
    "QueryInfo", "analyze_query", "classify",
    "register_testql_plugin",
]
