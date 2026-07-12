"""Tests for the `sql2testql` generator source (DDL → TestPlan)."""

from __future__ import annotations

from pathlib import Path

from sql2testql.source import SqlSource
from testql.ir import SqlStep


SQL_DDL = """\
CREATE TABLE users (id INT PRIMARY KEY, email VARCHAR(255));
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT);
"""


class TestSqlSource:
    def test_two_tables_yield_four_steps(self):
        plan = SqlSource().load(SQL_DDL)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        # 2 tables × 2 queries (count + sample) = 4
        assert len(sql_steps) == 4

    def test_count_step_has_assert(self):
        plan = SqlSource().load(SQL_DDL)
        users_count = next(s for s in plan.steps
                           if isinstance(s, SqlStep) and s.name == "count_users")
        assert any(a.op == ">=" for a in users_count.asserts)

    def test_schema_fixture_emitted(self):
        plan = SqlSource().load(SQL_DDL)
        assert any(f.name == "sql.schema" for f in plan.fixtures)

    def test_dialect_propagates(self):
        plan = SqlSource(dialect="postgres").load(SQL_DDL)
        for s in plan.steps:
            if isinstance(s, SqlStep):
                assert s.dialect == "postgres"

    def test_load_from_path(self, tmp_path: Path):
        p = tmp_path / "schema.sql"
        p.write_text(SQL_DDL, encoding="utf-8")
        plan = SqlSource().load(p)
        assert plan.steps


class TestRegistration:
    def test_source_resolved_via_entry_point(self):
        from testql.generators.sources import available_sources, get_source
        src = get_source("sql")
        assert src is not None
        assert type(src).__name__ == "SqlSource"
        assert "sql" in available_sources()
