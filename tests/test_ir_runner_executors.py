"""Tests for individual executors that don't need network access.

`api` / `graphql` / `encoder` make HTTP calls and are exercised separately with
mocks; here we focus on the deterministic, in-process executors.
"""

from __future__ import annotations

from textwrap import dedent

from testql.base import StepStatus
from testql.ir import (
    Assertion,
    EncoderStep,
    GraphqlStep,
    GuiStep,
    NlStep,
    ProtoStep,
    ShellStep,
    SqlStep,
    UnitStep,
)
from testql.ir_runner.context import ExecutionContext
from testql.ir_runner.executors import api, encoder, graphql, gui, nl, proto, shell, sql, unit


# ── sql ──────────────────────────────────────────────────────────────────────


class TestSqlExecutor:
    def test_dry_run(self):
        ctx = ExecutionContext(dry_run=True)
        result = sql.execute(SqlStep(query="SELECT 1", name="q"), ctx)
        assert result.status == StepStatus.PASSED
        assert result.details["dry_run"]

    def test_select_returns_columns(self):
        ctx = ExecutionContext()
        sql.execute(SqlStep(query="CREATE TABLE x (a INT, b INT)"), ctx)
        sql.execute(SqlStep(query="INSERT INTO x VALUES (1,2)"), ctx)
        result = sql.execute(SqlStep(query="SELECT a, b FROM x"), ctx)
        assert result.details["payload"]["rows"] == [{"a": 1, "b": 2}]
        assert result.details["payload"]["columns"] == ["a", "b"]

    def test_invalid_sql_returns_error(self):
        result = sql.execute(SqlStep(query="NOT VALID SQL"), ExecutionContext())
        assert result.status == StepStatus.ERROR


# ── shell ────────────────────────────────────────────────────────────────────


class TestShellExecutor:
    def test_zero_exit(self):
        result = shell.execute(ShellStep(command="echo ok"), ExecutionContext())
        assert result.status == StepStatus.PASSED

    def test_nonzero_warning(self):
        result = shell.execute(ShellStep(command="false"), ExecutionContext())
        assert result.status == StepStatus.WARNING

    def test_assertion_drives_status(self):
        step = ShellStep(
            command="echo 42",
            asserts=[Assertion(field="returncode", op="==", expected=0)],
        )
        result = shell.execute(step, ExecutionContext())
        assert result.status == StepStatus.PASSED


# ── proto ────────────────────────────────────────────────────────────────────


PROTO_SRC = dedent("""
    syntax = "proto3";
    message User {
      int64 id = 1;
      string email = 2;
      bool active = 3;
    }
""").strip()


class TestProtoExecutor:
    def test_round_trip(self, tmp_path):
        proto_file = tmp_path / "user.proto"
        proto_file.write_text(PROTO_SRC, encoding="utf-8")
        step = ProtoStep(
            schema_file=str(proto_file), message="User",
            fields={"_raw": "id:int64=1, email:string=a@b.c, active:bool=true"},
            check="round_trip_equal",
        )
        result = proto.execute(step, ExecutionContext())
        assert result.status == StepStatus.PASSED
        assert result.details["payload"]["valid"] is True

    def test_unknown_message(self, tmp_path):
        proto_file = tmp_path / "user.proto"
        proto_file.write_text(PROTO_SRC, encoding="utf-8")
        step = ProtoStep(schema_file=str(proto_file), message="Ghost",
                         check="round_trip_equal")
        result = proto.execute(step, ExecutionContext())
        assert result.status == StepStatus.ERROR
        assert "Ghost" in result.message

    def test_no_source(self):
        step = ProtoStep(message="User", check="round_trip_equal")
        result = proto.execute(step, ExecutionContext())
        assert result.status == StepStatus.ERROR


# ── nl + gui (skipped by design) ────────────────────────────────────────────


class TestSkippedExecutors:
    def test_nl_skipped(self):
        result = nl.execute(NlStep(text="click button"), ExecutionContext())
        assert result.status == StepStatus.SKIPPED

    def test_gui_skipped(self):
        result = gui.execute(GuiStep(action="click", selector="#x"),
                             ExecutionContext())
        assert result.status == StepStatus.SKIPPED

    def test_gui_dry_run_passes(self):
        result = gui.execute(GuiStep(action="click", selector="#x"),
                             ExecutionContext(dry_run=True))
        assert result.status == StepStatus.PASSED


# ── unit / encoder / graphql / api dry-run ──────────────────────────────────


class TestDryRunExecutors:
    def test_unit_dry_run(self):
        result = unit.execute(UnitStep(target="tests/x.py::y"),
                              ExecutionContext(dry_run=True))
        assert result.status == StepStatus.PASSED

    def test_unit_empty_target_errors(self):
        result = unit.execute(UnitStep(target=""), ExecutionContext())
        assert result.status == StepStatus.ERROR

    def test_encoder_dry_run(self):
        result = encoder.execute(EncoderStep(action="on"),
                                 ExecutionContext(dry_run=True))
        assert result.status == StepStatus.PASSED

    def test_encoder_unknown_action(self):
        result = encoder.execute(EncoderStep(action="dance"), ExecutionContext())
        assert result.status == StepStatus.ERROR

    def test_graphql_dry_run(self):
        result = graphql.execute(GraphqlStep(operation="query", body="{ me { id } }"),
                                 ExecutionContext(dry_run=True))
        assert result.status == StepStatus.PASSED

    def test_graphql_subscription_skipped(self):
        result = graphql.execute(
            GraphqlStep(operation="subscription", body="subscription{ x }"),
            ExecutionContext(),
        )
        assert result.status == StepStatus.SKIPPED

    def test_api_dry_run_url_resolution(self):
        ctx = ExecutionContext(dry_run=True, api_url="http://example.com")
        result = api.execute(
            type("S", (), {"path": "/foo", "method": "GET", "body": None,
                           "headers": {}, "name": "x", "asserts": [],
                           "kind": "api"})(),
            ctx,
        )
        assert result.details["url"] == "http://example.com/foo"
