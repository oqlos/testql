"""Tests for `testql.adapters.sql.sql_adapter`."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.sql import SqlDSLAdapter, parse, render
from testql.ir import SqlStep, Step, TestPlan


SAMPLE = """\
# SCENARIO: User table contract
# TYPE: sql
# DIALECT: postgres
# VERSION: 1.0

CONFIG[1]{key, value}:
  connection_url, postgresql://localhost/test_db

SCHEMA[3]{table, column, type}:
  users, id, INT
  users, email, VARCHAR(255)
  users, created_at, TIMESTAMP

QUERY[2]{name, sql}:
  count_users, SELECT COUNT(*) FROM users
  active_users, SELECT id FROM users WHERE active = true

ASSERT[3]{query, op, expected}:
  count_users, ==, 100
  active_users.length, >, 0
  active_users[0].id, !=, null
"""


class TestDetect:
    def test_by_extension(self, tmp_path: Path):
        p = tmp_path / "x.sql.testql.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        result = SqlDSLAdapter().detect(p)
        assert result.matches
        assert result.confidence >= 0.9

    def test_by_header(self):
        result = SqlDSLAdapter().detect(SAMPLE)
        assert result.matches

    def test_negative(self):
        assert not SqlDSLAdapter().detect("plain text\n").matches


class TestParseMetadata:
    def test_name(self):
        plan = parse(SAMPLE)
        assert plan.metadata.name == "User table contract"

    def test_type(self):
        plan = parse(SAMPLE)
        assert plan.metadata.type == "sql"

    def test_dialect_in_extra(self):
        plan = parse(SAMPLE)
        assert plan.metadata.extra.get("dialect") == "postgres"

    def test_default_dialect(self):
        plan = parse("# SCENARIO: x\n# TYPE: sql\n\nQUERY[1]{name, sql}:\n  q, SELECT 1\n")
        assert plan.metadata.extra.get("dialect") == "sqlite"


class TestParseConfig:
    def test_config_dict(self):
        plan = parse(SAMPLE)
        assert plan.config["connection_url"] == "postgresql://localhost/test_db"

    def test_connection_fixture_added(self):
        plan = parse(SAMPLE)
        names = [f.name for f in plan.fixtures]
        assert "sql.connection" in names


class TestParseSchema:
    def test_schema_fixture(self):
        plan = parse(SAMPLE)
        schemas = [f for f in plan.fixtures if f.name == "sql.schema"]
        assert len(schemas) == 1
        tables = schemas[0].setup["tables"]
        assert tables[0]["name"] == "users"
        assert len(tables[0]["columns"]) == 3


class TestParseQueries:
    def test_count_and_steps(self):
        plan = parse(SAMPLE)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        assert len(sql_steps) == 2

    def test_query_text(self):
        plan = parse(SAMPLE)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        assert sql_steps[0].name == "count_users"
        assert "COUNT(*)" in sql_steps[0].query
        assert sql_steps[1].name == "active_users"

    def test_dialect_propagated(self):
        plan = parse(SAMPLE)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        for s in sql_steps:
            assert s.dialect == "postgres"


class TestParseAsserts:
    def test_assert_attached_to_query(self):
        plan = parse(SAMPLE)
        sql_steps = {s.name: s for s in plan.steps if isinstance(s, SqlStep)}
        count_asserts = sql_steps["count_users"].asserts
        assert any(a.field == "count_users" and a.op == "==" and a.expected == 100
                   for a in count_asserts)

    def test_dotted_assert_attaches_to_base_query(self):
        plan = parse(SAMPLE)
        sql_steps = {s.name: s for s in plan.steps if isinstance(s, SqlStep)}
        active_asserts = sql_steps["active_users"].asserts
        fields = [a.field for a in active_asserts]
        assert "active_users.length" in fields
        assert "active_users[0].id" in fields

    def test_orphan_asserts_become_assert_step(self):
        plan = parse(
            "# SCENARIO: x\n# TYPE: sql\n\n"
            "ASSERT[1]{query, op, expected}:\n"
            "  unknown_query, ==, 1\n"
        )
        assert_steps = [s for s in plan.steps if s.kind == "assert"]
        assert assert_steps
        assert assert_steps[0].asserts[0].field == "unknown_query"


class TestRender:
    def test_round_trip_step_count(self):
        plan = parse(SAMPLE)
        rendered = render(plan)
        plan2 = parse(rendered)
        steps_orig = [s for s in plan.steps if isinstance(s, SqlStep)]
        steps_round = [s for s in plan2.steps if isinstance(s, SqlStep)]
        assert len(steps_orig) == len(steps_round)

    def test_render_includes_meta(self):
        plan = parse(SAMPLE)
        out = render(plan)
        assert "# TYPE: sql" in out
        assert "# DIALECT: postgres" in out

    def test_render_includes_schema(self):
        plan = parse(SAMPLE)
        out = render(plan)
        assert "SCHEMA[3]" in out
        assert "users" in out and "VARCHAR(255)" in out

    def test_render_empty_plan(self):
        out = render(TestPlan())
        # The renderer always emits "# TYPE: sql" for completeness.
        assert "# TYPE: sql" in out


class TestRegistration:
    def test_auto_registered(self):
        from testql.adapters import registry
        a = registry.get("sql")
        assert a is not None
        assert isinstance(a, SqlDSLAdapter)

    def test_extension_lookup(self, tmp_path: Path):
        from testql.adapters import registry
        p = tmp_path / "x.sql.testql.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        a = registry.by_extension(p)
        assert a is not None
        assert a.name == "sql"

    def test_extension_does_not_collide_with_testtoon(self, tmp_path: Path):
        # `.sql.testql.yaml` should pick "sql", NOT "testtoon" — even though
        # both share `.testql.yaml` family. Longest extension wins.
        from testql.adapters import registry
        p = tmp_path / "x.sql.testql.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        a = registry.by_extension(p)
        assert a is not None
        assert a.name == "sql"
