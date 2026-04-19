"""Tests for testql reporters: console, json, junit."""

import json
import xml.etree.ElementTree as ET

import pytest

from testql.base import ScriptResult, StepResult, StepStatus
from testql.reporters.console import report_console
from testql.reporters.json_reporter import report_json
from testql.reporters.junit import report_junit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(
    source="test.toon",
    ok=True,
    steps=None,
    errors=None,
    warnings=None,
    duration_ms=42.5,
) -> ScriptResult:
    return ScriptResult(
        source=source,
        ok=ok,
        steps=steps or [],
        errors=errors or [],
        warnings=warnings or [],
        duration_ms=duration_ms,
    )


def make_step(name="step1", status=StepStatus.PASSED, message="", duration_ms=1.0):
    return StepResult(name=name, status=status, message=message, duration_ms=duration_ms)


# ---------------------------------------------------------------------------
# Console reporter
# ---------------------------------------------------------------------------


class TestConsoleReporter:
    def test_returns_string(self):
        r = make_result()
        assert isinstance(report_console(r), str)

    def test_contains_source(self):
        r = make_result(source="my_test.toon")
        out = report_console(r)
        assert "my_test.toon" in out

    def test_passed_step_shows_checkmark(self):
        r = make_result(steps=[make_step("login", StepStatus.PASSED)])
        out = report_console(r)
        assert "login" in out
        assert "✅" in out

    def test_failed_step_shows_cross(self):
        r = make_result(ok=False, steps=[make_step("login", StepStatus.FAILED)])
        out = report_console(r)
        assert "❌" in out

    def test_error_step_shows_explosion(self):
        r = make_result(steps=[make_step("broken", StepStatus.ERROR)])
        out = report_console(r)
        assert "💥" in out

    def test_skipped_step_shows_icon(self):
        r = make_result(steps=[make_step("skip_me", StepStatus.SKIPPED)])
        out = report_console(r)
        assert "skip_me" in out

    def test_step_message_shown(self):
        step = make_step("check", StepStatus.FAILED, message="expected 200 got 404")
        r = make_result(ok=False, steps=[step])
        out = report_console(r)
        assert "expected 200 got 404" in out

    def test_errors_section_shown(self):
        r = make_result(ok=False, errors=["Timeout connecting to server"])
        out = report_console(r)
        assert "Timeout connecting to server" in out

    def test_summary_line_counts(self):
        steps = [make_step("a", StepStatus.PASSED), make_step("b", StepStatus.FAILED)]
        r = make_result(ok=False, steps=steps)
        out = report_console(r)
        assert "1/2" in out

    def test_duration_in_output(self):
        r = make_result(duration_ms=123.0)
        out = report_console(r)
        assert "123" in out


# ---------------------------------------------------------------------------
# JSON reporter
# ---------------------------------------------------------------------------


class TestJsonReporter:
    def test_returns_valid_json(self):
        r = make_result()
        out = report_json(r)
        data = json.loads(out)  # should not raise
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        r = make_result()
        data = json.loads(report_json(r))
        assert "source" in data
        assert "ok" in data
        assert "passed" in data
        assert "failed" in data
        assert "total" in data
        assert "steps" in data
        assert "errors" in data

    def test_source_matches(self):
        r = make_result(source="contract.toon")
        data = json.loads(report_json(r))
        assert data["source"] == "contract.toon"

    def test_step_fields(self):
        r = make_result(steps=[make_step("check", StepStatus.PASSED, "ok")])
        data = json.loads(report_json(r))
        assert len(data["steps"]) == 1
        step = data["steps"][0]
        assert step["name"] == "check"
        assert step["status"] == "passed"
        assert step["message"] == "ok"

    def test_counts(self):
        steps = [
            make_step("a", StepStatus.PASSED),
            make_step("b", StepStatus.FAILED),
            make_step("c", StepStatus.PASSED),
        ]
        r = make_result(ok=False, steps=steps)
        data = json.loads(report_json(r))
        assert data["passed"] == 2
        assert data["failed"] == 1
        assert data["total"] == 3

    def test_errors_included(self):
        r = make_result(errors=["boom"])
        data = json.loads(report_json(r))
        assert "boom" in data["errors"]

    def test_warnings_included(self):
        r = make_result(warnings=["slow"])
        data = json.loads(report_json(r))
        assert "slow" in data["warnings"]


# ---------------------------------------------------------------------------
# JUnit reporter
# ---------------------------------------------------------------------------


class TestJunitReporter:
    def test_returns_string(self):
        r = make_result()
        assert isinstance(report_junit(r), str)

    def test_valid_xml(self):
        r = make_result(steps=[make_step("step1")])
        out = report_junit(r)
        ET.fromstring(out)  # should not raise

    def test_testsuite_element(self):
        r = make_result(source="my.toon", steps=[make_step("s")])
        root = ET.fromstring(report_junit(r))
        assert root.tag == "testsuite" or root.find(".//testsuite") is not None

    def test_testcase_per_step(self):
        steps = [make_step("a"), make_step("b")]
        r = make_result(steps=steps)
        root = ET.fromstring(report_junit(r))
        testcases = root.findall(".//testcase") or ([root] if root.tag == "testcase" else [])
        assert len(testcases) >= 1

    def test_failure_element_for_failed_step(self):
        step = make_step("bad", StepStatus.FAILED, "expected 200")
        r = make_result(ok=False, steps=[step])
        out = report_junit(r)
        assert "failure" in out.lower() or "error" in out.lower()


# ---------------------------------------------------------------------------
# Base classes: VariableStore, InterpreterOutput, ScriptResult helpers
# ---------------------------------------------------------------------------

from testql._base_fallback import VariableStore, InterpreterOutput


class TestVariableStore:
    def test_set_get(self):
        vs = VariableStore()
        vs.set("x", 42)
        assert vs.get("x") == 42

    def test_default_if_missing(self):
        vs = VariableStore()
        assert vs.get("missing", "default") == "default"

    def test_has(self):
        vs = VariableStore({"a": 1})
        assert vs.has("a")
        assert not vs.has("b")

    def test_all(self):
        vs = VariableStore({"x": 1, "y": 2})
        assert vs.all() == {"x": 1, "y": 2}

    def test_clear(self):
        vs = VariableStore({"x": 1})
        vs.clear()
        assert vs.all() == {}

    def test_interpolate_curly(self):
        vs = VariableStore({"name": "alice"})
        assert vs.interpolate("Hello ${name}!") == "Hello alice!"

    def test_interpolate_dollar(self):
        vs = VariableStore({"host": "localhost"})
        assert vs.interpolate("http://$host:8000") == "http://localhost:8000"

    def test_interpolate_missing_left_unchanged(self):
        vs = VariableStore()
        assert vs.interpolate("${missing}") == "${missing}"

    def test_interpolate_no_vars(self):
        vs = VariableStore()
        assert vs.interpolate("plain text") == "plain text"

    def test_initial_values(self):
        vs = VariableStore({"k": "v"})
        assert vs.get("k") == "v"


class TestInterpreterOutput:
    def test_emit_stores_line(self):
        out = InterpreterOutput(quiet=True)
        out.emit("hello")
        assert "hello" in out.lines

    def test_ok_prefix(self):
        out = InterpreterOutput(quiet=True)
        out.ok("passed")
        assert any("passed" in l for l in out.lines)

    def test_fail_prefix(self):
        out = InterpreterOutput(quiet=True)
        out.fail("oops")
        assert any("oops" in l for l in out.lines)

    def test_warn_prefix(self):
        out = InterpreterOutput(quiet=True)
        out.warn("careful")
        assert any("careful" in l for l in out.lines)

    def test_info_prefix(self):
        out = InterpreterOutput(quiet=True)
        out.info("fyi")
        assert any("fyi" in l for l in out.lines)

    def test_error_prefix(self):
        out = InterpreterOutput(quiet=True)
        out.error("bad")
        assert any("bad" in l for l in out.lines)

    def test_step_with_icon(self):
        out = InterpreterOutput(quiet=True)
        out.step("🔵", "doing thing")
        assert any("doing thing" in l for l in out.lines)

    def test_not_quiet_prints(self, capsys):
        out = InterpreterOutput(quiet=False)
        out.emit("visible")
        captured = capsys.readouterr()
        assert "visible" in captured.out


class TestScriptResultHelpers:
    def test_passed_count(self):
        steps = [
            StepResult("a", StepStatus.PASSED),
            StepResult("b", StepStatus.FAILED),
            StepResult("c", StepStatus.PASSED),
        ]
        r = ScriptResult(source="test", ok=False, steps=steps)
        assert r.passed == 2

    def test_failed_count(self):
        steps = [
            StepResult("a", StepStatus.FAILED),
            StepResult("b", StepStatus.ERROR),
            StepResult("c", StepStatus.PASSED),
        ]
        r = ScriptResult(source="test", ok=False, steps=steps)
        assert r.failed == 2

    def test_summary_ok(self):
        r = ScriptResult(source="mysuite", ok=True, steps=[StepResult("a", StepStatus.PASSED)])
        s = r.summary()
        assert "mysuite" in s
        assert "✅" in s

    def test_summary_fail(self):
        r = ScriptResult(source="mysuite", ok=False, steps=[StepResult("b", StepStatus.FAILED)])
        s = r.summary()
        assert "❌" in s
