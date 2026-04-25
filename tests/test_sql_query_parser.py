"""Tests for `testql.adapters.sql.query_parser`."""

from __future__ import annotations

import pytest

from testql.adapters.sql.dialect_resolver import has_sqlglot
from testql.adapters.sql.query_parser import QueryInfo, analyze_query, classify


class TestClassify:
    def test_select(self):
        assert classify("SELECT 1") == "select"
        assert classify("  select * from t") == "select"

    def test_with_cte(self):
        assert classify("WITH cte AS (SELECT 1) SELECT * FROM cte") == "select"

    def test_insert(self):
        assert classify("INSERT INTO t VALUES (1)") == "insert"

    def test_update(self):
        assert classify("UPDATE t SET x=1") == "update"

    def test_delete(self):
        assert classify("DELETE FROM t") == "delete"

    def test_merge(self):
        assert classify("MERGE INTO t USING s ON ...") == "merge"

    def test_other(self):
        assert classify("CREATE TABLE t (id INT)") == "other"

    def test_empty(self):
        assert classify("") == "other"


class TestAnalyzeQueryRegexFallback:
    def test_basic_kind_set(self):
        info = analyze_query("SELECT 1")
        assert info.kind == "select"
        assert info.raw == "SELECT 1"


@pytest.mark.skipif(not has_sqlglot(), reason="sqlglot not installed")
class TestAnalyzeQuerySqlglot:
    def test_extracts_tables(self):
        info = analyze_query("SELECT id FROM users JOIN orders ON users.id = orders.user_id")
        assert "users" in info.tables
        assert "orders" in info.tables

    def test_extracts_columns(self):
        info = analyze_query("SELECT id, email FROM users")
        assert "id" in info.columns
        assert "email" in info.columns

    def test_formatted_present(self):
        info = analyze_query("select 1")
        assert info.formatted is not None
        assert "SELECT" in info.formatted.upper()

    def test_returns_kind_only_on_unparseable(self):
        # Non-SQL gibberish: sqlglot may raise; analyze_query must still return
        # a QueryInfo (kind only).
        info = analyze_query("not valid sql at all")
        assert isinstance(info, QueryInfo)
