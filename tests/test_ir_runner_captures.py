"""Runner-level tests for capture extraction + variable chaining."""

from __future__ import annotations

from testql.base import StepStatus
from testql.ir import (
    ApiStep,
    Capture,
    ScenarioMetadata,
    ShellStep,
    SqlStep,
    Step,
    TestPlan,
)
from testql.ir_runner import IRRunner, run_plan


def _plan(*steps: Step) -> TestPlan:
    return TestPlan(metadata=ScenarioMetadata(name="t", type="api"),
                    steps=list(steps))


# ── Captures from SQL steps ─────────────────────────────────────────────────


class TestSqlCaptures:
    def test_capture_from_first_row(self):
        plan = _plan(
            SqlStep(query="CREATE TABLE u (id INTEGER, name TEXT)"),
            SqlStep(query="INSERT INTO u VALUES (7, 'alice')"),
            SqlStep(
                query="SELECT id, name FROM u",
                captures=[
                    Capture(var_name="uid", from_path="rows.0.id"),
                    Capture(var_name="uname", from_path="rows.0.name"),
                ],
            ),
        )
        runner = IRRunner()
        result = runner.run(plan)
        assert result.ok
        assert runner.ctx.vars.get("uid") == 7
        assert runner.ctx.vars.get("uname") == "alice"

    def test_capture_chains_into_next_step(self):
        plan = _plan(
            SqlStep(query="CREATE TABLE u (id INTEGER)"),
            SqlStep(query="INSERT INTO u VALUES (42)"),
            SqlStep(
                query="SELECT id FROM u",
                captures=[Capture(var_name="uid", from_path="rows.0.id")],
            ),
            SqlStep(query="SELECT * FROM u WHERE id = ${uid}"),
        )
        result = run_plan(plan)
        assert result.ok
        assert result.steps[-1].details["payload"]["rowcount"] == 1


# ── Captures from shell steps ───────────────────────────────────────────────


class TestShellCaptures:
    def test_capture_returncode(self):
        plan = _plan(
            ShellStep(
                command="echo hello",
                captures=[
                    Capture(var_name="rc", from_path="returncode"),
                    Capture(var_name="out", from_path="stdout"),
                ],
            ),
        )
        runner = IRRunner()
        runner.run(plan)
        assert runner.ctx.vars.get("rc") == 0
        assert "hello" in runner.ctx.vars.get("out")


# ── Missing path → warning, not failure ─────────────────────────────────────


class TestMissingPath:
    def test_unknown_path_warns_but_passes(self):
        plan = _plan(
            SqlStep(query="CREATE TABLE u (id INTEGER)"),
            SqlStep(
                query="SELECT * FROM u",
                captures=[Capture(var_name="x", from_path="nonexistent.path")],
            ),
        )
        runner = IRRunner()
        result = runner.run(plan)
        assert result.ok
        assert runner.ctx.vars.get("x") is None
        assert any("not found" in w for w in result.warnings)


# ── Captures skipped on error/skipped steps ─────────────────────────────────


class TestErrorAndSkippedSteps:
    def test_error_step_does_not_capture(self):
        plan = _plan(
            SqlStep(
                query="NOT VALID SQL",
                captures=[Capture(var_name="x", from_path="anything")],
            ),
        )
        runner = IRRunner()
        result = runner.run(plan)
        assert result.steps[0].status == StepStatus.ERROR
        # No variable set, no warning emitted (capture pass was skipped).
        assert runner.ctx.vars.get("x") is None
        assert not any("capture" in w for w in result.warnings)


# ── Full chained API simulation via dry-run + manual step ───────────────────


class TestChainedInterpolation:
    def test_captured_value_interpolated_in_subsequent_step(self):
        """SQL → captures id → custom recording executor sees `${user_id}` resolved."""
        from testql.base import StepResult, StepStatus
        from testql.ir_runner.executors import register
        from testql.ir_runner.interpolation import interp_value

        recorded: dict = {}

        def record_executor(step, ctx):
            # Mirror the interpolation logic real executors run.
            recorded["path"] = interp_value(step.extra.get("path", ""), ctx.vars)
            return StepResult(name=step.name or "rec", status=StepStatus.PASSED)

        register("recording", record_executor)
        try:
            plan = _plan(
                SqlStep(query="CREATE TABLE u (id INTEGER)"),
                SqlStep(query="INSERT INTO u VALUES (99)"),
                SqlStep(
                    query="SELECT id FROM u",
                    captures=[Capture(var_name="user_id", from_path="rows.0.id")],
                ),
                Step(kind="recording", name="probe",
                     extra={"path": "/users/${user_id}"}),
            )
            result = run_plan(plan)
        finally:
            from testql.ir_runner.executors import _REGISTRY  # noqa: SLF001
            _REGISTRY.pop("recording", None)
        assert result.ok
        assert recorded["path"] == "/users/99"
