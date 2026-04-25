"""Tests for `testql.adapters.sql.ddl_parser`."""

from __future__ import annotations

import pytest

from testql.adapters.sql.ddl_parser import Column, ParsedDDL, Table, parse_ddl
from testql.adapters.sql.dialect_resolver import has_sqlglot


SIMPLE_DDL = """\
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT now,
    nickname VARCHAR(64)
);
"""

MULTI_TABLE_DDL = """\
CREATE TABLE users (id INT, email VARCHAR(255));
CREATE TABLE orders (id INT, user_id INT, total DECIMAL(10,2));
"""


class TestRegexFallback:
    def test_single_table(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        assert len(ddl.tables) == 1
        users = ddl.tables[0]
        assert users.name == "users"
        assert len(users.columns) == 4

    def test_column_types(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        users = ddl.table("users")
        assert users is not None
        types = {c.name: c.type for c in users.columns}
        assert types["id"].upper() == "INT"
        assert "VARCHAR" in types["email"].upper()

    def test_primary_key_flag(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        col = ddl.table("users").column("id")
        assert col is not None
        assert col.primary_key is True

    def test_not_null_flag(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        col = ddl.table("users").column("email")
        assert col is not None
        assert col.nullable is False

    def test_unique_flag(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        col = ddl.table("users").column("email")
        assert col.unique is True

    def test_default_extracted(self):
        ddl = parse_ddl(SIMPLE_DDL, prefer_sqlglot=False)
        col = ddl.table("users").column("created_at")
        assert col.default == "now"

    def test_multi_table(self):
        ddl = parse_ddl(MULTI_TABLE_DDL, prefer_sqlglot=False)
        names = [t.name for t in ddl.tables]
        assert names == ["users", "orders"]

    def test_empty_input(self):
        assert parse_ddl("", prefer_sqlglot=False).tables == []

    def test_to_dict(self):
        ddl = parse_ddl("CREATE TABLE t (id INT);", prefer_sqlglot=False)
        d = ddl.to_dict()
        assert d == {"tables": [{"name": "t", "columns": [
            {"name": "id", "type": "INT", "nullable": True,
             "primary_key": False, "unique": False, "default": None}
        ]}]}


@pytest.mark.skipif(not has_sqlglot(), reason="sqlglot not installed")
class TestSqlglotPath:
    def test_picks_sqlglot_by_default(self):
        ddl = parse_ddl(SIMPLE_DDL, dialect="postgres")
        assert ddl.tables, "sqlglot path returned no tables"
        users = ddl.table("users")
        assert users is not None
        assert any(c.primary_key for c in users.columns)

    def test_falls_back_on_unparseable(self):
        # Garbage input shouldn't raise — both paths must return ParsedDDL.
        ddl = parse_ddl("CREATE TABLE garbage", dialect="postgres")
        assert isinstance(ddl, ParsedDDL)


class TestTableHelpers:
    def test_column_lookup_case_insensitive(self):
        ddl = parse_ddl("CREATE TABLE t (Id INT);", prefer_sqlglot=False)
        t = ddl.table("T")
        assert t is not None
        assert t.column("ID") is not None

    def test_to_dict_round_trip(self):
        col = Column(name="x", type="INT", primary_key=True)
        d = col.to_dict()
        assert d["primary_key"] is True
        assert d["name"] == "x"
