"""Tests for `testql.ir_runner.engine` — `IRRunner` and `run_plan`."""

from __future__ import annotations

import pytest

from testql.base import StepStatus
from testql.ir import (
    ApiStep,
    Assertion,
    ScenarioMetadata,
    ShellStep,
    SqlStep,
    Step,
    TestPlan,
)
from testql.ir_runner import IRRunner, run_plan, supported_kinds
from testql.ir_runner.engine import load_plan
from testql.ir_runner.executors import register


def _plan(*steps: Step) -> TestPlan:
    return TestPlan(metadata=ScenarioMetadata(name="t", type="api"),
                    steps=list(steps))


# ── load_plan ────────────────────────────────────────────────────────────────


class TestLoadPlan:
    def test_passthrough_testplan(self):
        plan = _plan()
        assert load_plan(plan) is plan

    def test_unknown_source(self):
        with pytest.raises(ValueError):
            load_plan(12345)  # type: ignore[arg-type]


# ── core dispatch ────────────────────────────────────────────────────────────


class TestSupportedKinds:
    def test_all_step_kinds_have_executor(self):
        kinds = set(supported_kinds())
        # every IR step kind we ship must have an executor (or be deliberately
        # delegated, e.g. nl/gui as SKIPPED)
        assert {"api", "sql", "proto", "graphql", "shell",
                "encoder", "unit", "nl", "gui"} <= kinds


class TestEngineDryRun:
    def test_api_dry_run_does_not_call_network(self):
        plan = _plan(ApiStep(method="GET", path="/x", name="ping"))
        result = run_plan(plan, dry_run=True)
        assert result.ok
        assert result.steps[0].status == StepStatus.PASSED
        assert result.steps[0].details.get("dry_run") is True

    def test_summary_format(self):
        plan = _plan(ApiStep(method="GET", path="/x", name="ping"))
        result = run_plan(plan, dry_run=True)
        assert "ping" in result.steps[0].name
        assert result.passed == 1


class TestEngineSqlEndToEnd:
    def test_sqlite_in_memory_round_trip(self):
        plan = _plan(
            SqlStep(query="CREATE TABLE u (id INTEGER, name TEXT)", name="ddl"),
            SqlStep(query="INSERT INTO u VALUES (1,'a'),(2,'b')", name="seed",
                    asserts=[Assertion(field="rowcount", op="==", expected=2)]),
            SqlStep(query="SELECT * FROM u WHERE id=1", name="get",
                    asserts=[
                        Assertion(field="rowcount", op="==", expected=1),
                        Assertion(field="rows.0.name", op="==", expected="a"),
                    ]),
        )
        result = run_plan(plan)
        assert result.ok, [s.message for s in result.steps if not s.message == ""]

    def test_failing_assertion_makes_plan_not_ok(self):
        plan = _plan(
            SqlStep(query="CREATE TABLE u (id INTEGER)", name="ddl"),
            SqlStep(query="SELECT * FROM u", name="select",
                    asserts=[Assertion(field="rowcount", op="==", expected=99)]),
        )
        result = run_plan(plan)
        assert not result.ok
        assert any(s.status == StepStatus.FAILED for s in result.steps)
        assert "rowcount" in result.errors[0]


class TestEngineShell:
    def test_echo_succeeds(self):
        plan = _plan(ShellStep(command="echo hello", name="say"))
        result = run_plan(plan)
        assert result.ok
        assert "hello" in result.steps[0].details["payload"]["stdout"]

    def test_expect_exit_code(self):
        plan = _plan(ShellStep(command="false", name="fail",
                               expect_exit_code=1))
        result = run_plan(plan)
        # No assertions but expect_exit_code=1 → PASSED
        assert result.ok


class TestEngineUnknownKind:
    def test_unknown_kind_records_error(self):
        plan = _plan(Step(kind="totally-unknown", name="x"))
        result = run_plan(plan)
        assert not result.ok
        assert result.steps[0].status == StepStatus.ERROR
        assert "no executor" in result.steps[0].message


class TestRegisterCustomExecutor:
    def test_register_custom_kind(self):
        from testql.base import StepResult, StepStatus

        def my_executor(step, ctx):
            return StepResult(name=step.name or "custom",
                              status=StepStatus.PASSED, details={"ran": True})

        register("custom-x", my_executor)
        try:
            plan = _plan(Step(kind="custom-x", name="hi"))
            result = run_plan(plan)
            assert result.ok
            assert result.steps[0].details == {"ran": True}
        finally:
            from testql.ir_runner.executors import _REGISTRY  # noqa: SLF001
            _REGISTRY.pop("custom-x", None)


class TestRunnerVariables:
    def test_variables_persist_across_steps(self):
        runner = IRRunner(variables={"base": "foo"}, dry_run=True)
        result = runner.run(_plan(ApiStep(method="GET", path="/${base}", name="x")))
        # Even in dry-run the URL should have been interpolated
        assert "/foo" in result.steps[0].details.get("url", "")
