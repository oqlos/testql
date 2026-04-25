"""Tests for adapter-side `CAPTURE` section parsing + rendering.

Covers `TestToonAdapter` (API steps, indexed + named refs) and `SqlDSLAdapter`
(query-name refs).
"""

from __future__ import annotations

from textwrap import dedent

from testql.adapters.sql.sql_adapter import SqlDSLAdapter
from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.ir import ApiStep, SqlStep


# ── TestToon: CAPTURE by step index ─────────────────────────────────────────


TESTTOON_INDEXED = dedent("""\
# SCENARIO: capture-by-index
# TYPE: api

API[2]{method, endpoint, status}:
  POST, /devices, 201
  GET, /devices/${device_id}, 200

CAPTURE[1]{step, var, from}:
  1, device_id, data.id
""")


class TestTestToonCaptureByIndex:
    def test_parse_attaches_capture_to_first_step(self):
        plan = TestToonAdapter().parse(TESTTOON_INDEXED)
        assert len(plan.steps) == 2
        first, second = plan.steps
        assert isinstance(first, ApiStep)
        assert len(first.captures) == 1
        assert first.captures[0].var_name == "device_id"
        assert first.captures[0].from_path == "data.id"
        # Second step has no captures.
        assert second.captures == []

    def test_round_trip(self):
        adapter = TestToonAdapter()
        plan = adapter.parse(TESTTOON_INDEXED)
        rendered = adapter.render(plan)
        assert "CAPTURE[1]{step, var, from}:" in rendered
        assert "1, device_id, data.id" in rendered
        # Re-parse must preserve captures
        re_plan = adapter.parse(rendered)
        assert re_plan.steps[0].captures[0].var_name == "device_id"


# ── TestToon: CAPTURE by step name ──────────────────────────────────────────


TESTTOON_NAMED = dedent("""\
# SCENARIO: capture-by-name
# TYPE: api

API[1]{method, endpoint, status, name}:
  POST, /users, 201, createUser

CAPTURE[1]{step, var, from}:
  createUser, user_id, data.id
""")


class TestTestToonCaptureByName:
    def test_parse_attaches_via_step_name(self):
        plan = TestToonAdapter().parse(TESTTOON_NAMED)
        assert plan.steps[0].name == "createUser"
        assert plan.steps[0].captures[0].var_name == "user_id"


class TestUnresolvedCaptureSilentlyDropped:
    def test_unknown_target_is_ignored(self):
        toon = dedent("""\
            # SCENARIO: bad-ref
            # TYPE: api

            API[1]{method, endpoint, status}:
              GET, /x, 200

            CAPTURE[1]{step, var, from}:
              ghostStep, x, data.id
        """)
        plan = TestToonAdapter().parse(toon)
        # No exception, no capture attached.
        assert plan.steps[0].captures == []


# ── SQL: CAPTURE by query name ──────────────────────────────────────────────


SQL_SCENARIO = dedent("""\
# SCENARIO: sql-capture
# TYPE: sql
# DIALECT: sqlite

QUERY[2]{name, sql}:
  ddl, "CREATE TABLE u (id INTEGER, name TEXT)"
  list, "SELECT id, name FROM u"

CAPTURE[2]{query, var, from}:
  list, uid, rows.0.id
  list, uname, rows.0.name
""")


class TestSqlAdapterCapture:
    def test_parse_attaches_to_named_step(self):
        plan = SqlDSLAdapter().parse(SQL_SCENARIO)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        list_step = next(s for s in sql_steps if s.name == "list")
        assert len(list_step.captures) == 2
        assert {c.var_name for c in list_step.captures} == {"uid", "uname"}

    def test_round_trip_emits_capture_section(self):
        adapter = SqlDSLAdapter()
        plan = adapter.parse(SQL_SCENARIO)
        rendered = adapter.render(plan)
        assert "CAPTURE[2]" in rendered
        assert "list, uid, rows.0.id" in rendered

    def test_unknown_query_is_ignored(self):
        toon = dedent("""\
            # SCENARIO: bad-sql-ref
            # TYPE: sql

            QUERY[1]{name, sql}:
              q1, "SELECT 1"

            CAPTURE[1]{query, var, from}:
              ghostQuery, x, rows.0.x
        """)
        plan = SqlDSLAdapter().parse(toon)
        assert all(not s.captures for s in plan.steps if isinstance(s, SqlStep))


# ── End-to-end: parse → run → check captured variable ──────────────────────


class TestSqlCaptureExecutesEndToEnd:
    def test_parsed_capture_chains_through_runner(self):
        """The CAPTURE section yields working captures when run by IRRunner."""
        from testql.ir_runner import IRRunner

        toon = dedent("""\
            # SCENARIO: captured-chain
            # TYPE: sql
            # DIALECT: sqlite

            QUERY[3]{name, sql}:
              ddl, "CREATE TABLE u (id INTEGER)"
              seed, "INSERT INTO u VALUES (123)"
              get, "SELECT id FROM u"

            CAPTURE[1]{query, var, from}:
              get, the_id, rows.0.id
        """)
        plan = SqlDSLAdapter().parse(toon)
        runner = IRRunner()
        runner.run(plan)
        assert runner.ctx.vars.get("the_id") == 123
